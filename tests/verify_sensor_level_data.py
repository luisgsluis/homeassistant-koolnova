#!/usr/bin/env python3
"""
Verificación de que RSSI, online status y sync time están disponibles por sensor individual
"""

import json
import sys
import os

# Agregar el directorio del proyecto al path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from koolnova_api.client import KoolnovaAPIRestClient

def verify_sensor_level_data():
    """Verifica que los datos de conectividad están por sensor individual"""

    # Credenciales
    username = "luisgsluis@gmail.com"
    password = "aKOtur1!"
    email = username

    print("🔍 VERIFICACIÓN: DATOS DE CONECTIVIDAD POR SENSOR INDIVIDUAL")
    print("=" * 70)

    try:
        client = KoolnovaAPIRestClient(username, password, email)
        print("✅ Autenticación exitosa\n")

        # Obtener lista completa de dispositivos
        response = client._get_session().rest_request("GET", "devices/")
        devices = response.json()

        print(f"📊 Total dispositivos encontrados: {devices.get('total', 0)}")
        print("📋 ANÁLISIS POR SENSOR INDIVIDUAL:")
        print("-" * 70)

        sensor_data = []
        for i, device in enumerate(devices.get('data', []), 1):
            sensor = device.get('sensor', {})
            topic_info = sensor.get('topic_info', {})

            sensor_info = {
                'numero': i,
                'nombre': sensor.get('name', 'Sin nombre'),
                'sensor_id': sensor.get('id'),
                'topic_id': topic_info.get('id'),
                'is_online': topic_info.get('is_online'),
                'rssi': topic_info.get('rssi'),
                'last_sync': topic_info.get('last_sync'),
                'device_reference': topic_info.get('device_reference')
            }
            sensor_data.append(sensor_info)

            print(f"🏠 Sensor {i}: {sensor_info['nombre']}")
            print(f"   🆔 Sensor ID: {sensor_info['sensor_id']}")
            print(f"   📡 Topic ID: {sensor_info['topic_id']}")
            print(f"   🌐 Online: {sensor_info['is_online']}")
            print(f"   📶 RSSI: {sensor_info['rssi']} dBm")
            print(f"   🔄 Last Sync: {sensor_info['last_sync']}")
            print(f"   📱 Device Ref: {sensor_info['device_reference']}")
            print()

        print("📊 RESUMEN DE CONECTIVIDAD POR SENSOR:")
        print("-" * 70)

        online_count = sum(1 for s in sensor_data if s['is_online'] is True)
        total_sensors = len(sensor_data)

        print(f"✅ Sensores online: {online_count}/{total_sensors}")
        print(f"📶 RSSI promedio: {sum(s['rssi'] for s in sensor_data if s['rssi'] is not None) / len([s for s in sensor_data if s['rssi'] is not None]):.1f} dBm")

        # Verificar si todos tienen datos individuales
        all_have_rssi = all(s['rssi'] is not None for s in sensor_data)
        all_have_sync = all(s['last_sync'] is not None for s in sensor_data)
        all_have_online = all(s['is_online'] is not None for s in sensor_data)

        print(f"🔍 Todos tienen RSSI individual: {'✅ SÍ' if all_have_rssi else '❌ NO'}")
        print(f"🔍 Todos tienen sync time individual: {'✅ SÍ' if all_have_sync else '❌ NO'}")
        print(f"🔍 Todos tienen online status individual: {'✅ SÍ' if all_have_online else '❌ NO'}")

        print("\n🎯 CONCLUSIONES:")
        print("-" * 70)
        if all_have_rssi and all_have_sync and all_have_online:
            print("✅ CONFIRMADO: Los datos de conectividad (RSSI, online, sync) están disponibles")
            print("   POR CADA SENSOR INDIVIDUAL, no a nivel global del proyecto.")
            print()
            print("💡 Esto permite crear en Home Assistant:")
            print(f"   • {total_sensors} sensores individuales de RSSI")
            print(f"   • {total_sensors} sensores individuales de estado online")
            print(f"   • {total_sensors} sensores individuales de última sincronización")
            print(f"   • Monitoreo granular de conectividad por habitación")
        else:
            print("⚠️  Algunos sensores no tienen datos completos de conectividad")

        print("\n📈 VALOR AGREGADO:")
        print("-" * 70)
        print("• Diagnóstico individual de conectividad por habitación")
        print("• Detección de sensores con mala señal WiFi")
        print("• Monitoreo de sincronización por dispositivo")
        print("• Alertas específicas por sensor offline")

    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    verify_sensor_level_data()
