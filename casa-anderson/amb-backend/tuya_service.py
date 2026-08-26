"""
AMB Automação Residencial — TuyaService
Camada de integração com a API Tuya Cloud
"""
import hmac, hashlib, time, json, os, requests
from typing import Optional

# ─── CONFIGURAÇÃO ──────────────────────────────────────────────────────────
# Credenciais lidas de variáveis de ambiente (arquivo .env).
# O valor após a vírgula é apenas um fallback para não quebrar em dev local —
# REMOVA o fallback antes de publicar o backend online.
TUYA_CLIENT_ID = os.environ.get("TUYA_CLIENT_ID", "mar833ptq3ja3fstcwdg")
TUYA_SECRET    = os.environ.get("TUYA_SECRET", "27af5f3873a04fd191e1057615656d7a")
TUYA_BASE_URL  = os.environ.get("TUYA_BASE_URL", "https://openapi.tuyaus.com")  # América Ocidental


class TuyaService:
    def __init__(self):
        self._token: Optional[str] = None
        self._token_expires: float = 0

    # ── Assinatura HMAC-SHA256 ──────────────────────────────────────────────
    def _sign(self, t: int, access_token: str = "") -> str:
        msg = TUYA_CLIENT_ID + access_token + str(t)
        return hmac.new(
            TUYA_SECRET.encode(),
            msg.encode(),
            hashlib.sha256
        ).hexdigest().upper()

    # ── Headers padrão ─────────────────────────────────────────────────────
    def _headers(self, token: str = "") -> dict:
        t = int(time.time() * 1000)
        return {
            "client_id":   TUYA_CLIENT_ID,
            "sign":        self._sign(t, token),
            "t":           str(t),
            "sign_method": "HMAC-SHA256",
            "access_token": token,
            "Content-Type": "application/json",
        }

    # ── Token (auto-refresh) ────────────────────────────────────────────────
    def get_token(self) -> str:
        if self._token and time.time() < self._token_expires:
            return self._token
        r = requests.get(
            f"{TUYA_BASE_URL}/v1.0/token?grant_type=1",
            headers=self._headers(),
            timeout=10
        )
        data = r.json()
        if not data.get("success"):
            raise Exception(f"Tuya token error: {data}")
        self._token = data["result"]["access_token"]
        self._token_expires = time.time() + data["result"]["expire_time"] - 60
        return self._token

    # ── Listar todos os dispositivos de uma casa ────────────────────────────
    def get_devices(self, home_id: str) -> list:
        token = self.get_token()
        r = requests.get(
            f"{TUYA_BASE_URL}/v1.0/homes/{home_id}/devices",
            headers=self._headers(token),
            timeout=10
        )
        data = r.json()
        if not data.get("success"):
            raise Exception(f"Tuya devices error: {data}")
        return data["result"]

    # ── Status de um dispositivo ────────────────────────────────────────────
    def get_device_status(self, device_id: str) -> list:
        token = self.get_token()
        r = requests.get(
            f"{TUYA_BASE_URL}/v1.0/devices/{device_id}/status",
            headers=self._headers(token),
            timeout=10
        )
        return r.json().get("result", [])

    # ── Enviar comando para dispositivo ────────────────────────────────────
    def send_command(self, device_id: str, commands: list) -> bool:
        """
        Exemplos de commands:
          Liga luz:       [{"code": "switch_led", "value": True}]
          Dimmer 80%:     [{"code": "bright_value_v2", "value": 800}]  # 0-1000
          Temp. cor:      [{"code": "temp_value_v2", "value": 500}]    # 0-1000
          Persiana abre:  [{"code": "control", "value": "open"}]
          Persiana fecha: [{"code": "control", "value": "close"}]
          Persiana para:  [{"code": "control", "value": "stop"}]
          Tomada liga:    [{"code": "switch", "value": True}]
          AC liga:        [{"code": "switch", "value": True}]
          AC temp:        [{"code": "temp_set", "value": 23}]
        """
        token = self.get_token()
        payload = {"commands": commands}
        r = requests.post(
            f"{TUYA_BASE_URL}/v1.0/devices/{device_id}/commands",
            headers=self._headers(token),
            json=payload,
            timeout=10
        )
        data = r.json()
        return data.get("success", False)

    # ── Ativar cena ─────────────────────────────────────────────────────────
    def trigger_scene(self, home_id: str, scene_id: str) -> bool:
        token = self.get_token()
        r = requests.post(
            f"{TUYA_BASE_URL}/v1.0/homes/{home_id}/scenes/{scene_id}/trigger",
            headers=self._headers(token),
            timeout=10
        )
        return r.json().get("success", False)

    # ── Listar casas de um usuário (pelo UID do Smart Life) ─────────────────
    def get_user_homes(self, uid: str) -> list:
        token = self.get_token()
        r = requests.get(
            f"{TUYA_BASE_URL}/v1.0/users/{uid}/homes",
            headers=self._headers(token),
            timeout=10
        )
        return r.json().get("result", [])

    # ── Listar todos os dispositivos pelo UID ───────────────────────────────
    def get_devices_by_uid(self, uid: str) -> list:
        token = self.get_token()
        r = requests.get(
            f"{TUYA_BASE_URL}/v1.0/users/{uid}/devices",
            headers=self._headers(token),
            timeout=10
        )
        data = r.json()
        return data.get("result", [])


# Instância global
tuya = TuyaService()
