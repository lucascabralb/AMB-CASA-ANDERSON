"""
AMB Automação Residencial — Backend FastAPI
Casa Barbosa — Itapecerica da Serra

Execute:
    uvicorn main:app --host 0.0.0.0 --port 8000
"""

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import asyncio
import json
import logging

from tuya_service import tuya

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("amb")

app = FastAPI(title="AMB — Casa Barbosa", version="1.2.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ═══════════════════════════════════════════════════════════════════
# MAPEAMENTO REAL — Casa Barbosa
# ═══════════════════════════════════════════════════════════════════
DEVICES = {
    "sala_led": {"tuya_id": "ebd22738520fe4dbf0k1mx", "name": "Led Sala", "room": "Sala", "type": "dimmer"},
    "sala_spot": {"tuya_id": "eb82e540cf5adbb7ebas1x", "name": "Spot Sala", "room": "Sala", "type": "dimmer"},
    "sala_p1": {"tuya_id": "eb7f2b18dcf15c92248sg4", "name": "Persiana 1", "room": "Sala", "type": "blind"},
    "sala_p2": {"tuya_id": "eb7c18fbf9bf8dbfbeslwr", "name": "Persiana 2", "room": "Sala", "type": "blind"},
    "sala_controle": {"tuya_id": "042057708cce4ef81bce", "name": "Controle Sala", "room": "Sala", "type": "ir_remote"},

    "casal_luz": {"tuya_id": "ebeec9ea5f3a2ed357uotg", "name": "Luz Casal", "room": "Quarto Casal", "type": "switch"},
    "casal_persiana": {"tuya_id": "eb43af21f639037e69zo61", "name": "Persiana Casal", "room": "Quarto Casal", "type": "blind"},

    "meninas_luz": {"tuya_id": "eb34e21253b2de2a19ha0o", "name": "Luz Quarto Meninas", "room": "Quarto Meninas", "type": "switch"},
    "meninas_persiana": {"tuya_id": "eb8872973e4734339flhfa", "name": "Persiana Meninas", "room": "Quarto Meninas", "type": "blind"},

    "cozinha_luz": {"tuya_id": "eb9d1c4b04f5e2dd47etys", "name": "Luz Cozinha", "room": "Cozinha", "type": "switch"},
    "cozinha_persiana": {"tuya_id": "eba763d58413938126bmeg", "name": "Persiana Cozinha", "room": "Cozinha", "type": "blind"},

    "sacada_led_tv": {"tuya_id": "eb2df258e861f41b8cchyc", "name": "Led TV Sacada", "room": "Sacada", "type": "dimmer"},
    "sacada_luz_varanda": {"tuya_id": "eb9c826ec22c99f9edo2zg", "name": "Luz Varanda", "room": "Sacada", "type": "switch"},
    "sacada_cortina1": {"tuya_id": "eb986fcb7e3233fb9dkmg7", "name": "Cortina 1", "room": "Sacada", "type": "blind"},
    "sacada_cortina2": {"tuya_id": "eb41df6f0fcc82a6c5wbj7", "name": "Cortina 2", "room": "Sacada", "type": "blind"},
    "sacada_tv": {"tuya_id": "ebcf319fd81f66a612dwsg", "name": "TV Sacada", "room": "Sacada", "type": "switch"},
    "sacada_tv_controle": {"tuya_id": "ebd9a4e32f56539595zz6u", "name": "TV Sacada Controle", "room": "Sacada", "type": "ir_remote"},
    "sacada_ir_varanda": {"tuya_id": "ebc38f0b41f457cefbuzan", "name": "IR Varanda", "room": "Sacada", "type": "ir_remote"},
    "sacada_racao": {"tuya_id": "ebe0879bfc71858ff1qzfo", "name": "Ração", "room": "Sacada", "type": "feeder"},
    "sacada_camera": {"tuya_id": "eba9a57ce3bcb5db58nzpo", "name": "Câmera Sacada", "room": "Sacada", "type": "camera"},
    "sacada_freezer": {"tuya_id": "eb3370ddb28c3c3486bajp", "name": "Freezer", "room": "Sacada", "type": "plug"},
    "sacada_audio": {"tuya_id": "ebc8613bd19c139954edrb", "name": "Áudio", "room": "Sacada", "type": "switch"},

    "banheiro_luz": {"tuya_id": "eb794a5733410dcde97r3d", "name": "Luz Banheiro", "room": "Banheiro", "type": "switch"},
    "banheiro_exaustor": {"tuya_id": "eb871d43eed8bc5030itfw", "name": "Exaustor Banheiro", "room": "Banheiro", "type": "switch"},
    "banheiro_tomada": {"tuya_id": "eb5d934da2da71fd31qaw6", "name": "Tomada Banheiro", "room": "Banheiro", "type": "plug"},

    "lavanderia_interruptor": {"tuya_id": "eb7932fed1997606433pqf", "name": "Interruptor Lavanderia", "room": "Lavanderia", "type": "switch"},
    "lavanderia_rack": {"tuya_id": "eb1addc2656b668c03otmp", "name": "Refrigeração Rack", "room": "Lavanderia", "type": "plug"},
    "lavanderia_valvula": {"tuya_id": "eb930af2050554fc334zkm", "name": "Válvula Lavanderia", "room": "Lavanderia", "type": "switch"},

    "corredor_luz": {"tuya_id": "eb36e45857f1f348abfdwh", "name": "Luz Corredor", "room": "Corredor", "type": "switch"},
    "corredor_altar": {"tuya_id": "ebb0bba4a47a54232dltm4", "name": "Altar", "room": "Corredor", "type": "plug"},
    "corredor_escada": {"tuya_id": "eba8a922551fdc0230rzrc", "name": "Luz Escada", "room": "Corredor", "type": "switch"},

    "entrada_portao": {"tuya_id": "eb308a724d43066aed480v", "name": "Portão de Entrada", "room": "Entrada", "type": "lock"},
    "entrada_fechadura": {"tuya_id": "eb97d2ba3c0d62a8affbwr", "name": "Fechadura Entrada", "room": "Entrada", "type": "lock"},
    "entrada_alarme": {"tuya_id": "ebd04cdb891a2e92a2o8ew", "name": "Alarme", "room": "Entrada", "type": "alarm"},
}

SCENES = {
    "apple_tv_sala": {"name": "Apple TV Sala", "actions": [{"device": "sacada_tv", "cmd": "switch", "value": True}]},
    "persiana_cinema": {"name": "Persiana Cinema", "actions": [
        {"device": "sala_p1", "cmd": "blind", "value": "close"},
        {"device": "sala_p2", "cmd": "blind", "value": "close"},
    ]},
    "racao": {"name": "Ração", "actions": [{"device": "sacada_racao", "cmd": "feed", "value": 1}]},
    "abrir_persianas_cozinha": {"name": "Abrir Persianas Cozinha", "actions": [{"device": "cozinha_persiana", "cmd": "blind", "value": "open"}]},
    "fechar_persianas_cozinha": {"name": "Fechar Persianas Cozinha", "actions": [{"device": "cozinha_persiana", "cmd": "blind", "value": "close"}]},
    "fechar_cinema": {"name": "Fechar Cinema", "actions": [{"device": "sala_p1", "cmd": "blind", "value": "close"}]},
    "zona_3": {"name": "Ligar Zona 3", "actions": [{"device": "sacada_audio", "cmd": "switch", "value": True}]},
    "boa_noite": {"name": "Boa Noite", "actions": [
        {"device": "sala_led", "cmd": "switch", "value": False},
        {"device": "sala_spot", "cmd": "switch", "value": False},
        {"device": "casal_luz", "cmd": "switch", "value": False},
        {"device": "cozinha_luz", "cmd": "switch", "value": False},
        {"device": "sala_p1", "cmd": "blind", "value": "close"},
        {"device": "sala_p2", "cmd": "blind", "value": "close"},
        {"device": "casal_persiana", "cmd": "blind", "value": "close"},
    ]},
}


class SwitchCmd(BaseModel):
    device_id: str
    value: bool


class DimmerCmd(BaseModel):
    device_id: str
    brightness: int


class BlindCmd(BaseModel):
    device_id: str
    action: str


class SceneCmd(BaseModel):
    scene_id: str


@app.get("/")
def root():
    return {
        "app": "AMB Automação Residencial",
        "casa": "Casa Barbosa",
        "status": "online",
        "total_devices": len(DEVICES),
    }


@app.get("/health")
def health():
    return {"status": "ok", "service": "amb-backend"}


@app.get("/tuya-test")
def tuya_test():
    """Diagnóstico seguro: testa autenticação sem expor token ou secret."""
    try:
        info = tuya.test_connection()
        return {"success": True, **info}
    except Exception as e:
        logger.exception("Falha no teste Tuya")
        raise HTTPException(status_code=502, detail=str(e))


@app.get("/devices")
def list_devices():
    return {"devices": DEVICES}


@app.get("/rooms")
def get_rooms():
    rooms = {}
    for dev_id, dev in DEVICES.items():
        room = dev["room"]
        rooms.setdefault(room, []).append({"id": dev_id, **dev})
    return {"rooms": rooms}


@app.get("/devices/{device_id}/status")
def device_status(device_id: str):
    dev = DEVICES.get(device_id)
    if not dev:
        raise HTTPException(404, "Dispositivo não encontrado")
    try:
        status = tuya.get_device_status(dev["tuya_id"])
        return {"device_id": device_id, "name": dev["name"], "status": status}
    except Exception as e:
        logger.exception("Erro lendo status do dispositivo %s", device_id)
        raise HTTPException(502, f"Falha ao comunicar com a Tuya: {e}")


# ── Diagnóstico: mostra os códigos DP reais que um dispositivo reporta ──────
# Útil pra investigar qualquer dispositivo que não responder no futuro,
# sem precisar mexer em código: GET /devices/{device_id}/codes
@app.get("/devices/{device_id}/codes")
def device_codes(device_id: str):
    dev = DEVICES.get(device_id)
    if not dev:
        raise HTTPException(404, "Dispositivo não encontrado")
    try:
        status = tuya.get_device_status(dev["tuya_id"])
        return {
            "device_id": device_id,
            "name": dev["name"],
            "codes_disponiveis": [item.get("code") for item in status],
            "status_completo": status,
        }
    except Exception as e:
        logger.exception("Erro lendo códigos do dispositivo %s", device_id)
        raise HTTPException(502, f"Falha ao comunicar com a Tuya: {e}")


@app.get("/status/all")
def all_status():
    result = {}
    for dev_id, dev in DEVICES.items():
        try:
            status = tuya.get_device_status(dev["tuya_id"])
            result[dev_id] = {"name": dev["name"], "room": dev["room"], "status": status}
        except Exception as e:
            logger.exception("Erro lendo status %s", dev_id)
            result[dev_id] = {"name": dev["name"], "room": dev["room"], "error": str(e)}
    return result


@app.post("/switch")
def switch_device(cmd: SwitchCmd):
    dev = DEVICES.get(cmd.device_id)
    if not dev:
        raise HTTPException(404, "Dispositivo não encontrado")

    try:
        code = tuya.resolve_switch_code(dev["tuya_id"])
        ok = tuya.send_command(
            dev["tuya_id"],
            [{"code": code, "value": cmd.value}],
        )
    except Exception as e:
        logger.exception("Erro no /switch device=%s", cmd.device_id)
        raise HTTPException(502, f"Falha ao comunicar com a Tuya: {e}")

    return {"success": ok, "device": dev["name"], "value": cmd.value, "code_usado": code}


@app.post("/dimmer")
def set_dimmer(cmd: DimmerCmd):
    dev = DEVICES.get(cmd.device_id)
    if not dev:
        raise HTTPException(404, "Dispositivo não encontrado")
    if dev["type"] != "dimmer":
        raise HTTPException(400, "Dispositivo não é dimmer")

    if not 0 <= cmd.brightness <= 100:
        raise HTTPException(400, "brightness deve estar entre 0 e 100")

    tuya_brightness = int(cmd.brightness * 10)

    try:
        switch_code = tuya.resolve_switch_code(dev["tuya_id"])
        bright_code = tuya.resolve_brightness_code(dev["tuya_id"])
        commands = [
            {"code": switch_code, "value": True},
            {"code": bright_code, "value": tuya_brightness},
        ]
        ok = tuya.send_command(dev["tuya_id"], commands)
    except Exception as e:
        logger.exception("Erro no /dimmer device=%s", cmd.device_id)
        raise HTTPException(502, f"Falha ao comunicar com a Tuya: {e}")

    return {
        "success": ok, "device": dev["name"], "brightness": cmd.brightness,
        "codes_usados": {"switch": switch_code, "brightness": bright_code},
    }


@app.post("/blind")
def control_blind(cmd: BlindCmd):
    dev = DEVICES.get(cmd.device_id)
    if not dev:
        raise HTTPException(404, "Dispositivo não encontrado")
    if dev["type"] != "blind":
        raise HTTPException(400, "Dispositivo não é persiana/cortina")
    if cmd.action not in ("open", "close", "stop"):
        raise HTTPException(400, "Ação inválida: use open | close | stop")

    try:
        ok = tuya.send_command(
            dev["tuya_id"],
            [{"code": "control", "value": cmd.action}],
        )
    except Exception as e:
        logger.exception("Erro no /blind device=%s", cmd.device_id)
        raise HTTPException(502, f"Falha ao comunicar com a Tuya: {e}")

    return {"success": ok, "device": dev["name"], "action": cmd.action}


@app.post("/feed")
def feed_pet(device_id: str = "sacada_racao"):
    dev = DEVICES.get(device_id)
    if not dev:
        raise HTTPException(404, "Dispositivo não encontrado")

    try:
        ok = tuya.send_command(
            dev["tuya_id"],
            [{"code": "manual_feed", "value": 1}],
        )
    except Exception as e:
        logger.exception("Erro no /feed device=%s", device_id)
        raise HTTPException(502, f"Falha ao comunicar com a Tuya: {e}")

    return {"success": ok, "device": dev["name"]}


@app.post("/scene")
def trigger_scene(cmd: SceneCmd):
    scene = SCENES.get(cmd.scene_id)
    if not scene:
        raise HTTPException(404, "Cena não encontrada")

    results = []
    for action in scene["actions"]:
        dev = DEVICES.get(action["device"])
        if not dev:
            results.append({"device": action["device"], "success": False, "error": "Dispositivo não encontrado"})
            continue

        try:
            if action["cmd"] == "blind":
                commands = [{"code": "control", "value": action["value"]}]
            elif action["cmd"] == "switch":
                code = tuya.resolve_switch_code(dev["tuya_id"])
                commands = [{"code": code, "value": action["value"]}]
            elif action["cmd"] == "feed":
                commands = [{"code": "manual_feed", "value": action["value"]}]
            else:
                results.append({"device": dev["name"], "success": False, "error": "Ação desconhecida"})
                continue

            ok = tuya.send_command(dev["tuya_id"], commands)
            results.append({"device": dev["name"], "success": ok})
        except Exception as e:
            logger.exception("Erro na cena %s / dispositivo %s", cmd.scene_id, action["device"])
            results.append({"device": dev["name"], "success": False, "error": str(e)})

    return {"scene": scene["name"], "results": results}


@app.get("/scenes")
def list_scenes():
    return {"scenes": {k: v["name"] for k, v in SCENES.items()}}


connected = []


@app.websocket("/ws")
async def ws_endpoint(websocket: WebSocket):
    await websocket.accept()
    connected.append(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            for c in list(connected):
                if c != websocket:
                    try:
                        await c.send_text(data)
                    except Exception:
                        pass
    except WebSocketDisconnect:
        if websocket in connected:
            connected.remove(websocket)
