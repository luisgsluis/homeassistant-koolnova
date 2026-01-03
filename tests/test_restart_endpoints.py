#!/usr/bin/env python3
"""
Script para probar endpoints de reinicio/reconexión sin autenticación
"""

import subprocess
import json
import time
from typing import Dict, List

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
            "-m", "10",  # timeout 10 segundos
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
    elif code.startswith("ERROR"):
        return f"⚠️ ERROR: {code}"
    else:
        return f"🤔 OTRO: {code}"

def main():
    """Prueba todos los endpoints candidatos de reinicio/reconexión."""

    print("🔬 PRUEBA DE ENDPOINTS DE REINICIO/RECONEXIÓN")
    print("=" * 60)
    print("Patrón establecido:")
    print("  401 = ✅ Endpoint existe pero requiere autenticación")
    print("  404 = ❌ Endpoint no existe")
    print()

    # Endpoints candidatos organizados por categoría
    endpoints_by_category = {
        "🔄 HUB/CONTROLADORA": [
            "hub/123/restart",
            "hub/123/reboot",
            "hub/123/reset",
            "hub/restart",
            "hub/reboot",
            "hub/reset",
        ],
        "📡 MÓDULOS/DISPOSITIVOS": [
            "modules/123/reboot",
            "modules/123/reset",
            "modules/123/restart",
            "devices/123/reboot",
            "devices/123/reset",
            "devices/123/restart",
            "devices/123/reconnect",
        ],
        "🏠 TOPICS/PROYECTOS": [
            "topics/123/reconnect",
            "topics/123/reset",
            "topics/123/restart",
            "topics/reconnect",
            "projects/123/reconnect",
            "projects/123/reset",
            "projects/123/restart",
        ],
        "⚙️ SISTEMA": [
            "system/restart",
            "system/reset",
            "system/reboot",
            "system/reload",
            "system/network/reset",
            "system/mqtt/reconnect",
            "system/mqtt/reset",
        ],
        "🌐 CONEXIÓN/RED": [
            "network/reset",
            "network/restart",
            "network/reconnect",
            "connection/reset",
            "connection/restart",
            "wifi/reset",
            "wifi/reconnect",
        ],
        "🔧 CONFIGURACIÓN": [
            "config/reset",
            "config/restart",
            "config/reload",
            "settings/reset",
            "profile/reset",
        ],
        "📊 OTROS POSIBLES": [
            "admin/restart",
            "control/restart",
            "server/restart",
            "api/restart",
            "service/restart",
        ]
    }

    base_url = "https://api.koolnova.com/"
    all_results = {}

    for category, endpoints in endpoints_by_category.items():
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

            # Pequeña pausa para no sobrecargar
            time.sleep(0.5)

        all_results[category] = category_results

    # RESUMEN FINAL
    print("\n" + "="*60)
    print("📊 RESUMEN FINAL - ENDPOINTS QUE EXISTEN")
    print("="*60)

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
        print("2. Verificar qué métodos HTTP aceptan (GET, POST, PUT, PATCH)")
        print("3. Implementar los que funcionen en la integración")
        print("4. Documentar parámetros requeridos")

        # Guardar resultados en JSON
        with open('tests/restart_endpoints_results.json', 'w') as f:
            json.dump(all_results, f, indent=2, ensure_ascii=False)

        print("\n📄 Resultados guardados en: tests/restart_endpoints_results.json")
    else:
        print("\n❌ No se encontraron endpoints candidatos")

if __name__ == "__main__":
    main()
