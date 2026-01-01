#!/usr/bin/env python3
"""
Script para investigar métodos API adicionales de Koolnova
"""

import json
import sys
import os

# Agregar el directorio del proyecto al path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from koolnova_api.client import KoolnovaAPIRestClient
from koolnova_api.exceptions import KoolnovaError

def test_api_methods():
    """Prueba métodos API adicionales con credenciales"""

    # Credenciales desde variables de entorno
    username = os.getenv('KOOLNOVA_USERNAME')
    password = os.getenv('KOOLNOVA_PASSWORD')
    email = os.getenv('KOOLNOVA_EMAIL', username)  # Email por defecto es el username si es email

    if not username or not password:
        print("❌ ERROR: Credenciales no proporcionadas")
        print("\n💡 Para usar este script, establece las variables de entorno:")
        print("   export KOOLNOVA_USERNAME='tu_usuario_o_email'")
        print("   export KOOLNOVA_PASSWORD='tu_password'")
        print("   export KOOLNOVA_EMAIL='tu_email'  # opcional si username es email")
        print("\n   Ejemplo:")
        print("   export KOOLNOVA_USERNAME='usuario@ejemplo.com'")
        print("   export KOOLNOVA_PASSWORD='mipassword'")
        print("   python test_api_methods.py")
        return

    print("🔐 Intentando autenticación en Koolnova API...")
    print(f"Usuario: {username}")
    print(f"Email: {email}")

    try:
        client = KoolnovaAPIRestClient(username, password, email)

        # Probar métodos conocidos primero
        print("\n✅ Probando métodos ya implementados:")

        # Test projects
        try:
            projects = client.get_project()
            print(f"📋 Projects: {len(projects)} encontrados")
            if projects:
                print(f"   Primer proyecto: {projects[0].get('Project_Name', 'N/A')}")
        except Exception as e:
            print(f"   ❌ Projects error: {e}")

        # Test sensors
        try:
            sensors = client.get_sensors()
            print(f"🌡️ Sensors: {len(sensors)} encontrados")
            if sensors:
                print(f"   Primera zona: {sensors[0].get('Room_Name', 'N/A')}")
        except Exception as e:
            print(f"   ❌ Sensors error: {e}")

        print("\n🔍 Probando métodos adicionales descubiertos:")

        # Lista de endpoints adicionales para probar
        additional_endpoints = [
            'notifications',
            'devices',
            'users'
        ]

        for endpoint in additional_endpoints:
            try:
                print(f"\n📡 Probando /{endpoint}/")
                response = client._get_session().rest_request("GET", endpoint + "/")
                print(f"   ✅ Respuesta: {response.status_code}")
                if response.status_code == 200:
                    data = response.json()
                    print(f"   📊 Datos recibidos: {type(data)}")
                    if isinstance(data, dict):
                        print(f"   🔑 Keys principales: {list(data.keys())}")
                        # Mostrar detalles de paginación
                        if 'total' in data:
                            print(f"   📄 Total elementos: {data['total']}")
                        if 'data' in data and isinstance(data['data'], list):
                            print(f"   📝 Elementos en página: {len(data['data'])}")
                            if data['data'] and isinstance(data['data'][0], dict):
                                print(f"   🔍 Keys del primer elemento: {list(data['data'][0].keys())}")
                                # Mostrar algunos datos de ejemplo
                                first_item = data['data'][0]
                                print(f"   💡 Ejemplo - {endpoint}: {first_item}")
                    elif isinstance(data, list) and data:
                        print(f"   📝 Primer elemento keys: {list(data[0].keys()) if isinstance(data[0], dict) else 'No dict'}")
                        print(f"   📊 Total elementos: {len(data)}")
            except Exception as e:
                print(f"   ❌ Error en /{endpoint}/: {e}")

        # Probar métodos relacionados con módulos existentes
        print("\n🔧 Probando métodos relacionados con módulos existentes:")

        # Obtener IDs de módulos primero
        try:
            module_ids = client.search_all_ids()
            print(f"📟 IDs encontrados: {module_ids}")

            if module_ids['koolnova']:
                koolnova_id = module_ids['koolnova'][0]
                print(f"🎯 Probando con Koolnova ID: {koolnova_id}")

                # Probar endpoints relacionados con módulos
                module_endpoints = [
                    f'modules/{koolnova_id}/history',
                    f'modules/{koolnova_id}/logs',
                    f'modules/{koolnova_id}/measurements',
                    f'modules/{koolnova_id}/status',
                    f'modules/{koolnova_id}/diagnostics'
                ]

                for endpoint in module_endpoints:
                    try:
                        print(f"   📡 Probando /{endpoint}/")
                        response = client._get_session().rest_request("GET", endpoint)
                        print(f"      ✅ Respuesta: {response.status_code}")
                        if response.status_code == 200:
                            data = response.json()
                            print(f"      📊 Tipo de datos: {type(data)}")
                    except Exception as e:
                        print(f"      ❌ Error: {e}")

        except Exception as e:
            print(f"❌ Error obteniendo IDs de módulos: {e}")

    except Exception as e:
        print(f"❌ Error de autenticación: {e}")
        print("\n💡 Para usar este script:")
        print("   export KOOLNOVA_USERNAME='tu_usuario'")
        print("   export KOOLNOVA_PASSWORD='tu_password'")
        print("   export KOOLNOVA_EMAIL='tu_email'")
        print("   python test_api_methods.py")

if __name__ == "__main__":
    test_api_methods()
