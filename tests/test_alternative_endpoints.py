#!/usr/bin/env python3
"""
Script para probar endpoints alternativos de reinicio/reconexión
"""

import subprocess
import json
import time

def test_endpoint(url: str) -> str:
    """Prueba un endpoint y devuelve el código HTTP."""
    try:
        cmd = [
            "curl", "-s", "-o", "/dev/null", "-w", "%{http_code}",
            "-H", "User-Agent: Mozilla/5.0",
            "-H", "accept: application/json, text/plain, */*",
            "-H", "accept-language: fr",
            "-H", "origin: https://app.koolnova.com",
            "-H", "referer: https://app.koolnova.com/",
            "-m", "10",
            url
        ]

        result = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
        return result.stdout.strip()
    except Exception as e:
        return f"ERROR: {str(e)}"

def classify_response(code: str) -> str:
    """Clasifica la respuesta HTTP."""
    if code == "401":
        return "✅ EXISTE (requiere auth)"
    elif code == "403":
        return "✅ EXISTE (prohibido)"
    elif code == "404":
        return "❌ NO EXISTE"
    elif code == "405":
        return "✅ EXISTE (método no permitido)"
    elif code == "200":
        return "✅ EXISTE (acceso público)"
    elif code.startswith("ERROR"):
        return f"⚠️ ERROR: {code}"
    else:
        return f"🤔 OTRO: {code}"

def main():
    """Prueba endpoints alternativos de reinicio/reconexión."""

    print("🔬 PRUEBA DE ENDPOINTS ALTERNATIVOS DE REINICIO/RECONEXIÓN")
    print("=" * 70)

    # Endpoints alternativos basados en patrones comunes
    alternative_endpoints = {
        "🔄 CONTROL/POWER": [
            "control/restart", "control/reset", "control/reboot",
            "power/restart", "power/reset", "power/reboot",
            "manage/restart", "manage/reset", "manage/reboot",
        ],
        "🌐 NETWORKING": [
            "network/restart", "network/reset", "network/reload",
            "connection/restart", "connection/reset", "connection/reload",
            "connectivity/reset", "connectivity/restart",
            "interface/reset", "interface/restart",
        ],
        "📡 MQTT/COMMS": [
            "mqtt/restart", "mqtt/reset", "mqtt/reconnect", "mqtt/reload",
            "communication/reset", "communication/restart",
            "link/reset", "link/restart", "link/reconnect",
        ],
        "⚙️ MAINTENANCE": [
            "maintenance/restart", "maintenance/reset",
            "service/restart", "service/reset", "service/reload",
            "daemon/restart", "daemon/reset",
        ],
        "🔧 ADMIN": [
            "admin/restart", "admin/reset", "admin/reload",
            "superuser/restart", "superuser/reset",
            "root/restart", "root/reset",
        ],
        "📊 SYSTEM": [
            "system/control", "system/power", "system/manage",
            "platform/restart", "platform/reset",
            "core/restart", "core/reset", "core/reload",
        ],
        "🏠 HOME AUTOMATION": [
            "home/restart", "home/reset", "home/reload",
            "automation/restart", "automation/reset",
            "smart/restart", "smart/reset",
        ],
        "🔗 INTEGRATION": [
            "integration/restart", "integration/reset", "integration/reload",
            "api/restart", "api/reset", "api/reload",
            "endpoint/restart", "endpoint/reset",
        ]
    }

    base_url = "https://api.koolnova.com/"
    all_results = {}

    for category, endpoints in alternative_endpoints.items():
        print(f"\n{category}")
        print("-" * 50)

        category_results = {}
        for endpoint in endpoints:
            full_url = base_url + endpoint
            print(f"🔍 Probando: {endpoint}", end=" ... ")

            code = test_endpoint(full_url)
            classification = classify_response(code)
            print(f"{code} → {classification}")

            category_results[endpoint] = {
                "code": code,
                "classification": classification
            }

            time.sleep(0.3)  # Pausa más corta

        all_results[category] = category_results

    # RESUMEN FINAL
    print("\n" + "="*70)
    print("📊 RESUMEN FINAL - ENDPOINTS ALTERNATIVOS")
    print("="*70)

    existing_endpoints = []
    for category, results in all_results.items():
        category_existing = []
        for endpoint, data in results.items():
            if "EXISTE" in data["classification"]:
                category_existing.append(endpoint)

        if category_existing:
            print(f"\n{category}:")
            for endpoint in category_existing:
                print(f"  ✅ {endpoint}")

            existing_endpoints.extend(category_existing)

    print(f"\n🎯 TOTAL ENDPOINTS CANDIDATOS ENCONTRADOS: {len(existing_endpoints)}")

    if existing_endpoints:
        print("\n💡 PRÓXIMOS PASOS:")
        print("1. Probar estos endpoints con credenciales válidas")
        print("2. Verificar métodos HTTP (GET, POST, PUT, PATCH)")
        print("3. Verificar si requieren parámetros adicionales")
        print("4. Implementar los que funcionen")

        # Guardar resultados
        with open('tests/alternative_endpoints_results.json', 'w') as f:
            json.dump(all_results, f, indent=2, ensure_ascii=False)

        print("\n📄 Resultados guardados en: tests/alternative_endpoints_results.json")
    else:
        print("\n❌ No se encontraron endpoints candidatos alternativos")
        print("💡 La API de Koolnova parece ser más básica de lo esperado")

if __name__ == "__main__":
    main()
