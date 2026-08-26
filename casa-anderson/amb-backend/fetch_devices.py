"""
AMB — Busca automática de dispositivos Tuya
Execute este script para listar todos os dispositivos da conta
e pegar os Device IDs necessários para configurar o main.py

Uso: python3 fetch_devices.py <UID_do_usuario>

O UID do usuário fica em:
  App Smart Life → Perfil → clica no ícone do usuário → UID aparece abaixo do nome
  Ou: iot.tuya.com → Cloud → Devices → Link by App Account → UID
"""
import sys
from tuya_service import tuya
import json

def main():
    uid = sys.argv[1] if len(sys.argv) > 1 else None

    print("=" * 60)
    print("  AMB — Buscando dispositivos Tuya")
    print("=" * 60)

    # 1. Obter token
    print("\n1. Autenticando...")
    token = tuya.get_token()
    print(f"   ✓ Token obtido: {token[:20]}...")

    # 2. Listar dispositivos
    if uid:
        print(f"\n2. Buscando dispositivos do usuário {uid}...")
        devices = tuya.get_devices_by_uid(uid)
    else:
        print("\n2. UID não informado.")
        print("   Execute: python3 fetch_devices.py SEU_UID")
        print("\n   Como encontrar seu UID:")
        print("   App Smart Life → Perfil → toque no ícone do usuário")
        return

    print(f"\n   Encontrados: {len(devices)} dispositivos\n")
    print("-" * 60)

    for dev in devices:
        print(f"  Nome:      {dev.get('name', 'Sem nome')}")
        print(f"  Device ID: {dev.get('id', '?')}")
        print(f"  Categoria: {dev.get('category', '?')}")
        print(f"  Online:    {'✓' if dev.get('online') else '✗'}")
        print(f"  Modelo:    {dev.get('model', '?')}")
        print()

    # Exportar JSON
    with open("devices_found.json", "w") as f:
        json.dump(devices, f, indent=2, ensure_ascii=False)
    print(f"\n✓ Salvo em: devices_found.json")
    print("\nCopie os Device IDs para o main.py")

if __name__ == "__main__":
    main()
