#!/usr/bin/env python3
"""
Debug script para diagnosticar por qué no aparecen los atributos de conectividad
en la entidad KoolnovaProjectEntity
"""

import sys
import os
import json
from datetime import datetime
from collections import Counter

# Agregar el directorio del proyecto al path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from koolnova_api.client import KoolnovaAPIRestClient

def debug_entity_attributes():
    """Simula exactamente la lógica de extra_state_attributes de KoolnovaProjectEntity"""

    # Credenciales
    username = "luisgsluis@gmail.com"
    password = "aKOtur1!"
    email = username

    print("🔬 DEBUG: Simulando extra_state_attributes() de KoolnovaProjectEntity")
    print("=" * 80)

    try:
        client = KoolnovaAPIRestClient(username, password, email)
        print("✅ Autenticación exitosa\n")

        # 1. SIMULAR _update_project_data()
        print("📋 1. OBTENIENDO DATOS DEL PROYECTO:")
        projects = client.get_project()
        project = projects[0] if projects else None
        print(f"   Proyecto encontrado: {project.get('Project_Name') if project else 'None'}")
        print(f"   Topic_ID: {project.get('Topic_id') if project else 'None'}")
        print(f"   is_online: {project.get('is_online') if project else 'None'}")
        print(f"   last_sync: {project.get('last_sync') if project else 'None'}")
        print()

        # 2. SIMULAR obtención de sensores
        print("🏠 2. OBTENIENDO DATOS DE SENSORES:")
        sensors = client.get_sensors()
        sensors_count = len(sensors)
        print(f"   Total sensores: {sensors_count}")

        if sensors:
            print("   Primer sensor - Keys disponibles:")
            first_sensor = sensors[0]
            print(f"   🔑 {list(first_sensor.keys())}")

            # Verificar si tiene topic_info
            if 'topic_info' in first_sensor:
                print("   ✅ topic_info SÍ existe")
                topic_info = first_sensor['topic_info']
                print(f"   📡 topic_info keys: {list(topic_info.keys())}")

                # Verificar campos específicos
                rssi = topic_info.get('rssi')
                is_online = topic_info.get('is_online')
                last_sync = topic_info.get('last_sync')

                print(f"   📶 RSSI: {rssi}")
                print(f"   🌐 is_online: {is_online}")
                print(f"   🔄 last_sync: {last_sync}")
            else:
                print("   ❌ topic_info NO existe en el sensor")
        print()

        # 3. SIMULAR LA LÓGICA DE extra_state_attributes()
        print("⚙️ 3. SIMULANDO extra_state_attributes():")
        print("-" * 50)

        # Recrear exactamente la lógica del método
        attrs = {
            "eco_mode": project["eco"] if project else None,
            "is_stop": project.get("is_stop") if project else None,
            "total_zones": sensors_count,
            "control_type": "global_controller",
        }

        print(f"   Atributos base: {attrs}")

        # Lógica de zone breakdowns
        zone_status_breakdown = {}
        zone_fan_breakdown = {}
        for sensor in sensors:
            status = sensor.get("Room_status", "02")
            # Simular el mapeo (simplificado para debug)
            hvac_mode = "auto"  # Simplificado
            zone_status_breakdown[hvac_mode] = zone_status_breakdown.get(hvac_mode, 0) + 1

            fan_speed = sensor.get("Room_speed", "4")
            fan_mode = "auto"  # Simplificado
            zone_fan_breakdown[fan_mode] = zone_fan_breakdown.get(fan_mode, 0) + 1

        attrs["zones_status_breakdown"] = zone_status_breakdown
        attrs["zones_fan_breakdown"] = zone_fan_breakdown

        print(f"   Zone breakdowns añadidos: status={zone_status_breakdown}, fan={zone_fan_breakdown}")

        # LÓGICA CRÍTICA: Obtener datos de conectividad del sistema
        print("\n🔍 4. LÓGICA CRÍTICA - DATOS DE CONECTIVIDAD:")
        print("-" * 50)

        system_connectivity = {}
        if sensors:
            print(f"   ✅ Hay {len(sensors)} sensores disponibles")
            topic_info = sensors[0].get("topic_info", {})
            print(f"   📡 topic_info obtenido: {bool(topic_info)}")

            if topic_info:
                system_connectivity = {
                    "system_rssi": topic_info.get("rssi"),
                    "online_status": topic_info.get("is_online"),
                    "last_sync": topic_info.get("last_sync"),
                }
                print(f"   🔧 system_connectivity creado: {system_connectivity}")
            else:
                print("   ❌ topic_info está vacío")
        else:
            print("   ❌ No hay sensores disponibles")

        # Agregar datos de conectividad del sistema (desde sensores)
        print("\n📝 5. AGREGANDO ATRIBUTOS DE CONECTIVIDAD:")
        print("-" * 50)

        connectivity_added = 0
        if system_connectivity.get("system_rssi") is not None:
            attrs["system_rssi"] = system_connectivity["system_rssi"]
            connectivity_added += 1
            print(f"   ✅ system_rssi añadido: {system_connectivity['system_rssi']}")

        if system_connectivity.get("online_status") is not None:
            attrs["online_status"] = system_connectivity["online_status"]
            connectivity_added += 1
            print(f"   ✅ online_status añadido: {system_connectivity['online_status']}")

        if system_connectivity.get("last_sync"):
            try:
                attrs["last_sync"] = datetime.fromisoformat(system_connectivity["last_sync"])
                connectivity_added += 1
                print(f"   ✅ last_sync añadido: {system_connectivity['last_sync']} (convertido a datetime)")
            except (ValueError, TypeError) as e:
                attrs["last_sync"] = system_connectivity["last_sync"]
                connectivity_added += 1
                print(f"   ⚠️ last_sync añadido sin conversión: {system_connectivity['last_sync']} (error: {e})")

        print(f"\n📊 TOTAL ATRIBUTOS DE CONECTIVIDAD AÑADIDOS: {connectivity_added}/3")

        # 6. RESULTADO FINAL
        print("\n🎯 6. RESULTADO FINAL - ATRIBUTOS QUE SE DEVOLVERÍAN:")
        print("-" * 50)

        print("Atributos que aparecerían en Home Assistant:")
        for key, value in sorted(attrs.items()):
            if key in ['system_rssi', 'online_status', 'last_sync']:
                print(f"   🎯 {key}: {value} ← ESTE ES UNO DE LOS BUSCADOS")
            else:
                print(f"   📋 {key}: {value}")

        # Verificación final
        has_rssi = 'system_rssi' in attrs
        has_online = 'online_status' in attrs
        has_sync = 'last_sync' in attrs

        print("\n✅ VERIFICACIÓN FINAL:")
        print(f"   system_rssi presente: {'✅ SÍ' if has_rssi else '❌ NO'}")
        print(f"   online_status presente: {'✅ SÍ' if has_online else '❌ NO'}")
        print(f"   last_sync presente: {'✅ SÍ' if has_sync else '❌ NO'}")

        if has_rssi and has_online and has_sync:
            print("\n🎉 ÉXITO: Los 3 atributos aparecerían correctamente")
        else:
            print("\n❌ ERROR: Faltan atributos - revisar logs anteriores")
            # Mostrar qué falta
            missing = []
            if not has_rssi: missing.append('system_rssi')
            if not has_online: missing.append('online_status')
            if not has_sync: missing.append('last_sync')
            print(f"   Faltan: {missing}")

    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    debug_entity_attributes()
