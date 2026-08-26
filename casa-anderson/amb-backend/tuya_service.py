"""
AMB Automação Residencial — TuyaService
Integração com a Tuya Cloud API v1.0.

IMPORTANTE:
- Configure TUYA_CLIENT_ID, TUYA_SECRET e TUYA_BASE_URL nas Variables da Railway.
- NÃO coloque credenciais reais no código.
- TUYA_BASE_URL deve corresponder ao data center do projeto Tuya.
"""

import hashlib
import hmac
import json
import logging
import os
import time
from typing import Optional
from urllib.parse import urlsplit

import requests

logger = logging.getLogger("tuya")


class TuyaAPIError(Exception):
    """Erro retornado pela Tuya ou erro de comunicação."""


class TuyaService:
    # ── Candidatos de código DP, em ordem de prioridade ─────────────────────
    # Cada categoria/modelo Tuya usa um nome diferente para "ligar/desligar"
    # e para "intensidade". Em vez de adivinhar por tipo de dispositivo,
    # consultamos o status real do device e usamos o código que ele reporta.
    SWITCH_CODE_CANDIDATES = [
        "switch_led", "switch_led_1", "switch_1", "switch", "switch_neon",
        "switch_countdown", "light", "switch_usb1",
    ]
    BRIGHTNESS_CODE_CANDIDATES = [
        "bright_value_v2", "bright_value", "bright_value_v1",
    ]

    def __init__(self):
        self.client_id = self._required_env("TUYA_CLIENT_ID")
        self.secret = self._required_env("TUYA_SECRET")
        self.base_url = os.environ.get(
            "TUYA_BASE_URL",
            "https://openapi.tuyaus.com",
        ).rstrip("/")

        self._token: Optional[str] = None
        self._token_expires: float = 0

    @staticmethod
    def _required_env(name: str) -> str:
        value = os.environ.get(name)
        if not value:
            raise RuntimeError(
                f"Variável de ambiente obrigatória não configurada: {name}"
            )
        return value.strip()

    def _content_sha256(self, body: str = "") -> str:
        return hashlib.sha256(body.encode("utf-8")).hexdigest()

    def _string_to_sign(
        self,
        method: str,
        path_with_query: str,
        body: str = "",
        signed_headers: str = "",
    ) -> str:
        return "\n".join(
            [
                method.upper(),
                self._content_sha256(body),
                signed_headers,
                path_with_query,
            ]
        )

    def _sign(
        self,
        timestamp_ms: int,
        method: str,
        path_with_query: str,
        body: str = "",
        access_token: str = "",
        signed_headers: str = "",
    ) -> str:
        string_to_sign = self._string_to_sign(
            method,
            path_with_query,
            body,
            signed_headers,
        )
        message = (
            self.client_id
            + access_token
            + str(timestamp_ms)
            + string_to_sign
        )
        return hmac.new(
            self.secret.encode("utf-8"),
            message.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest().upper()

    def _headers(
        self,
        method: str,
        path_with_query: str,
        body: str = "",
        token: str = "",
    ) -> dict:
        timestamp_ms = int(time.time() * 1000)

        return {
            "client_id": self.client_id,
            "sign": self._sign(
                timestamp_ms,
                method,
                path_with_query,
                body,
                token,
            ),
            "t": str(timestamp_ms),
            "sign_method": "HMAC-SHA256",
            "Content-Type": "application/json",
        } | ({"access_token": token} if token else {})

    def _request(
        self,
        method: str,
        path: str,
        *,
        token: str = "",
        body: Optional[str] = None,
        timeout: int = 15,
    ) -> dict:
        if body is None:
            body = ""

        url = self.base_url + path
        headers = self._headers(method, path, body, token)

        logger.info("Tuya request %s %s", method.upper(), path)

        try:
            response = requests.request(
                method=method.upper(),
                url=url,
                headers=headers,
                data=body if body else None,
                timeout=timeout,
            )
        except requests.RequestException as exc:
            raise TuyaAPIError(
                f"Erro de conexão com a Tuya ({self.base_url}): {exc}"
            ) from exc

        # Evita que uma resposta HTML/proxy cause um JSONDecodeError confuso.
        content_type = response.headers.get("content-type", "")
        try:
            data = response.json()
        except ValueError:
            preview = response.text[:500].replace("\n", " ")
            raise TuyaAPIError(
                f"Tuya respondeu HTTP {response.status_code} "
                f"sem JSON. Content-Type={content_type!r}; "
                f"resposta={preview!r}"
            )

        if response.status_code >= 400:
            raise TuyaAPIError(
                f"Tuya HTTP {response.status_code}: {data}"
            )

        if not data.get("success", False):
            raise TuyaAPIError(
                f"Tuya API rejeitou a requisição: {data}"
            )

        return data

    def get_token(self) -> str:
        if self._token and time.time() < self._token_expires:
            return self._token

        path = "/v1.0/token?grant_type=1"
        data = self._request("GET", path, timeout=15)

        result = data.get("result") or {}
        token = result.get("access_token")
        expire_time = result.get("expire_time", 0)

        if not token:
            raise TuyaAPIError(
                f"Resposta de token sem access_token: {data}"
            )

        self._token = token
        self._token_expires = time.time() + max(int(expire_time) - 60, 30)

        logger.info("Token Tuya obtido com sucesso.")
        return token

    def test_connection(self) -> dict:
        """Testa autenticação sem expor token, secret ou dados sensíveis."""
        token = self.get_token()
        return {
            "tuya_api": "reachable",
            "base_url": self.base_url,
            "token_received": bool(token),
            "token_expires_in_seconds": max(
                0, int(self._token_expires - time.time())
            ),
        }

    def get_devices(self, home_id: str) -> list:
        token = self.get_token()
        path = f"/v1.0/homes/{home_id}/devices"
        data = self._request("GET", path, token=token)
        return data.get("result") or []

    def get_device_status(self, device_id: str) -> list:
        token = self.get_token()
        path = f"/v1.0/devices/{device_id}/status"
        data = self._request("GET", path, token=token)
        return data.get("result") or []

    # ── Descobre o código DP correto de "ligar/desligar" do dispositivo ─────
    def resolve_switch_code(self, device_id: str) -> str:
        """
        Cada categoria de dispositivo Tuya usa um nome de código diferente
        pra ligar/desligar (switch_led, switch_1, switch...). Em vez de
        adivinhar, consultamos o status atual do dispositivo e usamos
        o código que ele realmente reporta.
        """
        try:
            status = self.get_device_status(device_id)
            codes_disponiveis = {item.get("code") for item in status}
            for candidato in self.SWITCH_CODE_CANDIDATES:
                if candidato in codes_disponiveis:
                    return candidato
            logger.warning(
                "Nenhum código de switch conhecido encontrado para %s. "
                "Códigos disponíveis: %s", device_id, codes_disponiveis
            )
        except Exception:
            logger.exception("Falha ao resolver switch code de %s", device_id)
        return "switch_1"  # fallback mais comum em interruptores de parede

    # ── Descobre o código DP correto de "intensidade" (dimmer/LED) ──────────
    def resolve_brightness_code(self, device_id: str) -> str:
        try:
            status = self.get_device_status(device_id)
            codes_disponiveis = {item.get("code") for item in status}
            for candidato in self.BRIGHTNESS_CODE_CANDIDATES:
                if candidato in codes_disponiveis:
                    return candidato
            logger.warning(
                "Nenhum código de brilho conhecido encontrado para %s. "
                "Códigos disponíveis: %s", device_id, codes_disponiveis
            )
        except Exception:
            logger.exception("Falha ao resolver brightness code de %s", device_id)
        return "bright_value_v2"  # fallback mais comum

    def send_command(self, device_id: str, commands: list) -> bool:
        token = self.get_token()
        path = f"/v1.0/devices/{device_id}/commands"
        body = json.dumps(
            {"commands": commands},
            separators=(",", ":"),
            ensure_ascii=False,
        )

        data = self._request(
            "POST",
            path,
            token=token,
            body=body,
            timeout=15,
        )

        return bool(data.get("success", False))

    def trigger_scene(self, home_id: str, scene_id: str) -> bool:
        token = self.get_token()
        path = f"/v1.0/homes/{home_id}/scenes/{scene_id}/trigger"
        data = self._request("POST", path, token=token, body="")
        return bool(data.get("success", False))

    def get_user_homes(self, uid: str) -> list:
        token = self.get_token()
        path = f"/v1.0/users/{uid}/homes"
        data = self._request("GET", path, token=token)
        return data.get("result") or []

    def get_devices_by_uid(self, uid: str) -> list:
        token = self.get_token()
        path = f"/v1.0/users/{uid}/devices"
        data = self._request("GET", path, token=token)
        return data.get("result") or []


tuya = TuyaService()
