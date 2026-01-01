#!/usr/bin/env python3
"""
Análisis de qué datos son específicos de habitación vs datos del controlador global
"""

import json
import sys
import os

# Agregar el directorio del proyecto al path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from koolnova_api.client import KoolnovaAPIRestClient

def analyze_room_specific_data():
    """Analiza qué datos son específicos de habitación vs globales"""

    # Credenciales
    username = "luisgsluis@gmail.com"
    password = "aKOtur1!"
    email = username

    print("🔍 ANÁLISIS: DATOS ESPECÍFICOS DE HABITACIÓN vs DATOS GLOBALES")
    print("=" * 80)

    try:
        client = KoolnovaAPIRestClient(username, password, email)
        print("✅ Autenticación exitosa\n")

        # Obtener lista completa de dispositivos
        response = client._get_session().rest_request("GET", "devices/")
        devices = response.json()

        print("📊 ANALIZANDO LOS 8 SENSORES PARA IDENTIFICAR DATOS ESPECÍFICOS:")
        print("-" * 80)

        # Recopilar datos de todos los sensores
        sensor_analysis = []
        global_data = {}
        room_specific_data = {}

        for i, device in enumerate(devices.get('data', []), 1):
            sensor = device.get('sensor', {})
            topic_info = sensor.get('topic_info', {})

            sensor_data = {
                'numero': i,
                'nombre': sensor.get('name', 'Sin nombre'),
                'temperatura': sensor.get('temperature'),
                'setpoint': sensor.get('setpoint_temperature'),
                'status': sensor.get('status'),
                'zona': sensor.get('zone'),
                'speed': sensor.get('speed'),
                'is_trv': sensor.get('is_trv'),
                'is_removed': sensor.get('is_removed'),
                # Datos que sospechamos son globales del controlador
                'rssi': topic_info.get('rssi'),
                'is_online': topic_info.get('is_online'),
                'last_sync': topic_info.get('last_sync'),
                'device_reference': topic_info.get('device_reference'),
                'mqtt_address': topic_info.get('mqtt_address'),
                'mqtt_security': topic_info.get('mqtt_security'),
                'topic_id': topic_info.get('id'),
                'ssid': topic_info.get('ssid')
            }
            sensor_analysis.append(sensor_data)

        # Mostrar datos por sensor
        print("🏠 DATOS POR SENSOR:")
        for sensor in sensor_analysis:
            print(f"\n🏠 Sensor {sensor['numero']}: {sensor['nombre']}")
            print(f"   🌡️ Temperatura: {sensor['temperatura']}°C")
            print(f"   🎯 Setpoint: {sensor['setpoint']}°C")
            print(f"   📊 Status: {sensor['status']} (HVAC)")
            print(f"   🏷️ Zona: {sensor['zona']}")
            print(f"   🌬️ Speed: {sensor['speed']} (ventilador)")
            print(f"   📶 RSSI: {sensor['rssi']} dBm")
            print(f"   🌐 Online: {sensor['is_online']}")
            print(f"   🔄 Last Sync: {sensor['last_sync']}")
            print(f"   📱 Device Ref: {sensor['device_reference']}")

        print("\n" + "="*80)
        print("🔍 ANÁLISIS DE DATOS GLOBALES vs ESPECÍFICOS DE HABITACIÓN:")
        print("-" * 80)

        # Verificar qué datos son iguales en todos los sensores (datos globales)
        global_fields = []
        room_fields = []

        # Comparar valores entre sensores
        if len(sensor_analysis) >= 2:
            first_sensor = sensor_analysis[0]

            for field in ['rssi', 'is_online', 'last_sync', 'device_reference', 'mqtt_address', 'mqtt_security', 'topic_id', 'ssid']:
                all_same = all(sensor[field] == first_sensor[field] for sensor in sensor_analysis)
                if all_same:
                    global_fields.append(field)
                    print(f"🌐 GLOBAL: {field} = {first_sensor[field]} (igual en todos los sensores)")
                else:
                    room_fields.append(field)
                    print(f"🏠 ESPECÍFICO: {field} varía entre sensores")

            print("\n📊 CAMPOS TEMPERATURA/HVAC:")
            for field in ['temperatura', 'setpoint', 'status', 'zona', 'speed']:
                values = [sensor[field] for sensor in sensor_analysis]
                unique_values = list(set(values))
                if len(unique_values) > 1:
                    room_fields.append(field)
                    print(f"🏠 ESPECÍFICO: {field} = {unique_values} (varía por habitación)")
                else:
                    global_fields.append(field)
                    print(f"🌐 GLOBAL: {field} = {unique_values[0]} (igual en todos)")

        print("\n" + "="*80)
        print("🎯 CONCLUSIONES:")
        print("-" * 80)

        print("❌ DATOS GLOBALES DEL CONTROLADOR D43 (iguales en todos los sensores):")
        for field in global_fields:
            if field == 'rssi':
                print("   📶 RSSI: Calidad de señal WiFi del controlador")
            elif field == 'is_online':
                print("   🌐 Online status: Conectividad del controlador a internet")
            elif field == 'last_sync':
                print("   🔄 Last sync: Última comunicación del controlador con la nube")
            elif field == 'device_reference':
                print("   📱 Device reference: ID del controlador central")
            elif field == 'mqtt_address':
                print("   🔗 MQTT address: Servidor MQTT del controlador")
            elif field == 'mqtt_security':
                print("   🔒 MQTT security: Configuración de seguridad")
            elif field == 'topic_id':
                print("   📡 Topic ID: Identificador del topic MQTT")
            elif field == 'ssid':
                print("   📶 SSID: Nombre de la red WiFi")

        print("\n✅ DATOS ESPECÍFICOS DE HABITACIÓN (diferentes por sensor):")
        for field in room_fields:
            if field == 'temperatura':
                print("   🌡️ Temperatura: Cada sensor mide su habitación")
            elif field == 'setpoint':
                print("   🎯 Setpoint: Temperatura objetivo por habitación")
            elif field == 'status':
                print("   📊 Status: Modo HVAC por habitación (COOL/HEAT/OFF/AUTO)")
            elif field == 'zona':
                print("   🏷️ Zona: Identificación de zona por habitación")
            elif field == 'speed':
                print("   🌬️ Speed: Velocidad del ventilador por habitación")

        print("\n💡 VALOR REAL PARA HOME ASSISTANT:")
        print("-" * 80)
        print("• Los datos 'específicos de habitación' SÍ existen y son útiles")
        print("• Temperatura, setpoint, status HVAC, zona, speed - varían por habitación")
        print("• RSSI, online, sync - son del controlador, no de habitaciones")
        print("• Se pueden crear sensores de temperatura individuales por habitación")
        print("• El RSSI global indica calidad de conexión del sistema completo")

    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    analyze_room_specific_data()
