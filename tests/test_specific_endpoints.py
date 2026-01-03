#!/usr/bin/env python3
"""
Script para probar endpoints específicos de reinicio y explorar redirecciones
"""

import subprocess
import json
import time

def test_endpoint_full(url: str, method: str = "GET") -> dict:
    """Prueba un endpoint y devuelve información completa incluyendo headers de redirección."""
    try:
        cmd = [
            "curl", "-s", "-I", "-X", method,  # -I para headers, -X para método
            "-H", "User-Agent: Mozilla/5.0",
            "-H", "accept: application/json, text/plain, */*",
            "-H", "accept-language: fr",
            "-H", "origin: https://app.koolnova.com",
            "-H", "referer: https://app.koolnova.com/",
            "-L",  # Seguir redirecciones
            "-m", "10",
            url
        ]

        result = subprocess.run(cmd, capture_output=True, text=True, timeout=15)

        # Parsear respuesta
        response_lines = result.stdout.strip().split('\n')
        status_line = response_lines[0] if response_lines else ""
        headers = {}

        for line in response_lines[1:]:
            if ': ' in line:
                key, value = line.split(': ', 1)
                headers[key.lower()] = value

        return {
            "url": url,
            "method": method,
            "status_line": status_line,
            "status_code": status_line.split(' ')[1] if len(status_line.split(' ')) > 1 else "UNKNOWN",
            "headers": headers,
            "location": headers.get("location"),
            "final_url": headers.get("location") or url
        }

    except Exception as e:
        return {
            "url": url,
            "method": method,
            "error": str(e)
        }

def main():
    """Prueba endpoints específicos y explora redirecciones."""

    print("🔬 PRUEBA DE ENDPOINTS ESPECÍFICOS Y REDIRECCIONES")
    print("=" * 70)

    # Endpoints específicos para probar
    specific_endpoints = [
        # Topics específicos (ya que sabemos que /topics/ existe)
        ("topics/reboot", "GET"),
        ("topics/reboot", "POST"),
        ("topics/restart", "GET"),
        ("topics/restart", "POST"),
        ("topics/reset", "GET"),
        ("topics/reset", "POST"),
        ("topics/reload", "GET"),
        ("topics/reload", "POST"),

        # Más variaciones
        ("topics/control", "GET"),
        ("topics/power", "GET"),
        ("topics/manage", "GET"),
        ("topics/admin", "GET"),

        # Proyectos
        ("projects/restart", "GET"),
        ("projects/reset", "GET"),
        ("projects/reconnect", "GET"),

        # Admin con diferentes métodos
        ("admin/", "GET"),
        ("admin/", "POST"),
        ("admin/restart", "GET"),
        ("admin/restart", "POST"),
        ("admin/login/", "GET"),
        ("admin/login/", "POST"),

        # Más admin
        ("admin/auth/", "GET"),
        ("admin/logout/", "GET"),
        ("admin/password_change/", "GET"),

        # API admin
        ("api/admin/", "GET"),
        ("api/admin/restart", "POST"),

        # Django admin patterns
        ("admin/koolnova/", "GET"),
        ("admin/koolnova/topic/", "GET"),
        ("admin/koolnova/project/", "GET"),

        # System
        ("system/admin", "GET"),
        ("system/control", "GET"),
        ("system/manage", "GET"),

        # Control directo
        ("control/", "GET"),
        ("control/system", "GET"),
        ("control/restart", "POST"),
        ("control/reset", "POST"),

        # Management
        ("manage/", "GET"),
        ("manage/system", "GET"),
        ("manage/control", "GET"),
        ("manage/restart", "POST"),

        # Power
        ("power/", "GET"),
        ("power/control", "GET"),
        ("power/restart", "POST"),
        ("power/reset", "POST"),
    ]

    base_url = "https://api.koolnova.com/"
    all_results = []

    print(f"Probando {len(specific_endpoints)} endpoints específicos...")
    print()

    for i, (endpoint, method) in enumerate(specific_endpoints, 1):
        full_url = base_url + endpoint
        print("2d", end="")

        result = test_endpoint_full(full_url, method)
        result["endpoint"] = endpoint

        all_results.append(result)

        # Pequeña pausa
        time.sleep(0.2)

    print("\n" + "="*70)
    print("📊 ANÁLISIS DE RESULTADOS")
    print("="*70)

    # Clasificar resultados
    redirects_302 = []
    not_found_404 = []
    unauthorized_401 = []
    other_responses = []

    for result in all_results:
        code = result.get("status_code", "ERROR")
        endpoint = result["endpoint"]
        method = result["method"]

        if code == "302":
            redirects_302.append((endpoint, method, result.get("location", "UNKNOWN")))
        elif code == "404":
            not_found_404.append((endpoint, method))
        elif code == "401":
            unauthorized_401.append((endpoint, method))
        else:
            other_responses.append((endpoint, method, code))

    # Mostrar resultados
    print(f"🔄 REDIRECCIONES 302 (posiblemente admin): {len(redirects_302)}")
    for endpoint, method, location in redirects_302:
        print(f"   {method} {endpoint} → {location}")

    print(f"\n✅ AUTORIZACIÓN REQUERIDA 401: {len(unauthorized_401)}")
    for endpoint, method in unauthorized_401:
        print(f"   {method} {endpoint}")

    print(f"\n❌ NO ENCONTRADO 404: {len(not_found_404)}")
    for endpoint, method in not_found_404:
        print(f"   {method} {endpoint}")

    if other_responses:
        print(f"\n🤔 OTRAS RESPUESTAS: {len(other_responses)}")
        for endpoint, method, code in other_responses:
            print(f"   {method} {endpoint} → {code}")

    # Análisis especial de redirecciones admin
    print("\n🎯 ANÁLISIS DE REDIRECCIONES ADMIN")
    print("-" * 40)

    admin_redirects = [r for r in redirects_302 if "admin" in r[0]]
    if admin_redirects:
        print("Redirecciones admin encontradas:")
        for endpoint, method, location in admin_redirects:
            print(f"   {method} {endpoint}")
            print(f"   → Redirige a: {location}")

            # Verificar si es login de Django
            if "login" in location or "admin" in location:
                print("   💡 Posiblemente login de administración Django")
            print()
    else:
        print("No se encontraron redirecciones admin específicas")

    # Guardar resultados detallados
    with open('tests/specific_endpoints_results.json', 'w') as f:
        json.dump(all_results, f, indent=2, ensure_ascii=False)

    print(f"\n📄 Resultados detallados guardados en: tests/specific_endpoints_results.json")

    # Conclusiones
    print("\n🎯 CONCLUSIONES:")
    print("-" * 40)

    if unauthorized_401:
        print(f"✅ {len(unauthorized_401)} endpoints requieren autenticación (posiblemente existen)")

    if redirects_302:
        print(f"🔄 {len(redirects_302)} endpoints redirigen (posiblemente a login admin)")

    if not_found_404:
        print(f"❌ {len(not_found_404)} endpoints no existen")

    print("\n💡 Los endpoints que requieren autenticación podrían existir")
    print("   y funcionar con credenciales válidas de administrador.")

if __name__ == "__main__":
    main()
