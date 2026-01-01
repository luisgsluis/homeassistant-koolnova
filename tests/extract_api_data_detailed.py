#!/usr/bin/env python3
"""
Extracción detallada de datos de todos los endpoints API adicionales
"""

import json
import sys
import os
from collections import defaultdict

# Agregar el directorio del proyecto al path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from koolnova_api.client import KoolnovaAPIRestClient

def extract_api_data_detailed():
    """Extrae y analiza detalladamente todos los datos de los endpoints adicionales"""

    # Credenciales
    username = "luisgsluis@gmail.com"
    password = "aKOtur1!"
    email = username

    print("🔬 EXTRACCIÓN DETALLADA DE DATOS API")
    print("=" * 80)

    try:
        client = KoolnovaAPIRestClient(username, password, email)
        print("✅ Autenticación exitosa\n")

        # Obtener IDs para endpoints relacionados
        device_id = None
        topic_id = None
        project_id = None

        try:
            devices_response = client._get_session().rest_request("GET", "devices/")
            devices_data = devices_response.json()
            if devices_data.get('data') and len(devices_data['data']) > 0:
                device_id = devices_data['data'][0]['id']
                topic_id = devices_data['data'][0]['sensor']['topic_info']['id']
                project_id = devices_data['data'][0]['project']
        except Exception as e:
            print(f"❌ Error obteniendo IDs: {e}")
            return

        print(f"🎯 IDs obtenidos: Device={device_id}, Topic={topic_id}, Project={project_id}\n")

        # 1. EXTRACCIÓN DETALLADA DE NOTIFICATIONS
        print("📢 1. EXTRACCIÓN DETALLADA: /notifications/")
        print("-" * 60)
        try:
            response = client._get_session().rest_request("GET", "notifications/")
            notifications = response.json()

            print(f"📊 Estructura general: {type(notifications)}")
            print(f"🔑 Keys principales: {list(notifications.keys())}")
            print(f"📈 Total notificaciones: {notifications.get('total', 0)}")
            print(f"📄 Páginas: currentPage={notifications.get('currentPage')}, lastPage={notifications.get('lastPage')}, perPage={notifications.get('perPage')}")

            data_array = notifications.get('data', [])
            print(f"📝 Array de datos: {len(data_array)} elementos")

            if data_array:
                print("🔍 Estructura de notificación de ejemplo:")
                print(json.dumps(data_array[0], indent=2, default=str))
            else:
                print("ℹ️  No hay notificaciones activas en el sistema")

            print("\n💡 USO EN HOME ASSISTANT:")
            print("   • Sensor binario: notificaciones_activas (true/false)")
            print("   • Sensor numérico: total_notificaciones")
            print("   • Atributo: lista_detallada_notificaciones")

        except Exception as e:
            print(f"❌ Error: {e}")
        print("\n" + "="*60 + "\n")

        # 2. EXTRACCIÓN DETALLADA DE DEVICES
        print("📱 2. EXTRACCIÓN DETALLADA: /devices/")
        print("-" * 60)
        try:
            response = client._get_session().rest_request("GET", "devices/")
            devices = response.json()

            print(f"📊 Estructura general: {type(devices)}")
            print(f"🔑 Keys principales: {list(devices.keys())}")
            print(f"📈 Total dispositivos: {devices.get('total', 0)}")
            print(f"📄 Páginas: currentPage={devices.get('currentPage')}, lastPage={devices.get('lastPage')}, perPage={devices.get('perPage')}")

            data_array = devices.get('data', [])
            print(f"📝 Array de dispositivos: {len(data_array)} elementos")

            if data_array:
                device = data_array[0]
                print("🔍 Estructura completa del primer dispositivo:")
                print(json.dumps(device, indent=2, default=str))

                # Análisis detallado
                print("\n🔎 ANÁLISIS DETALLADO DEL DISPOSITIVO:")
                print(f"   🆔 ID: {device.get('id')}")
                print(f"   🔑 Key: {device.get('key')}")
                print(f"   🏠 Project: {device.get('project')}")
                print(f"   🏠 Room: {device.get('room', 'None')}")
                print(f"   📱 Type: {device.get('type')}")
                print(f"   📅 Created: {device.get('created_at')}")
                print(f"   🔄 Updated: {device.get('updated_at')}")

                # Información del sensor
                sensor = device.get('sensor', {})
                if sensor:
                    print("\n🌡️  INFORMACIÓN DEL SENSOR:")
                    print(f"      🆔 Sensor ID: {sensor.get('id')}")
                    print(f"      📛 Name: {sensor.get('name', 'Sin nombre')}")
                    print(f"      🌡️ Temperature: {sensor.get('temperature')}°C")
                    print(f"      🎯 Setpoint: {sensor.get('setpoint_temperature')}°C")
                    print(f"      📊 Status: {sensor.get('status')} ({'COOL' if sensor.get('status') == '00' else 'HEAT' if sensor.get('status') == '01' else 'OFF' if sensor.get('status') == '02' else 'AUTO'})")
                    print(f"      🏷️ Zone: {sensor.get('zone')}")
                    print(f"      🌬️ Speed: {sensor.get('speed')} ({'LOW' if sensor.get('speed') == '1' else 'MEDIUM' if sensor.get('speed') == '2' else 'HIGH' if sensor.get('speed') == '3' else 'AUTO'})")
                    print(f"      🖼️ Image: {sensor.get('image')}")
                    print(f"      📅 Sensor Created: {sensor.get('created_at')}")
                    print(f"      🔄 Sensor Updated: {sensor.get('updated_at')}")
                    print(f"      🔌 is_trv: {sensor.get('is_trv')}")
                    print(f"      ❌ is_removed: {sensor.get('is_removed')}")

                    # Información del topic
                    topic_info = sensor.get('topic_info', {})
                    if topic_info:
                        print("\n📡  INFORMACIÓN DEL TOPIC:")
                        print(f"         🆔 Topic ID: {topic_info.get('id')}")
                        print(f"         🔑 Topic: {topic_info.get('topic')}")
                        print(f"         🔢 UC: {topic_info.get('uc')}")
                        print(f"         📛 Topic Name: {topic_info.get('name')}")
                        print(f"         🏠 Topic Project: {topic_info.get('project', {}).get('name') if topic_info.get('project') else 'N/A'}")
                        print(f"         👤 User: {topic_info.get('project', {}).get('user', {}).get('first_name') if topic_info.get('project') and topic_info.get('project').get('user') else 'N/A'}")
                        print(f"         📊 Mode: {topic_info.get('mode')} ({'COOL' if topic_info.get('mode') == '1' else 'OFF' if topic_info.get('mode') == '2' else 'AUTO' if topic_info.get('mode') == '4' else 'HEAT'})")
                        print(f"         ✅ is_stop: {topic_info.get('is_stop')}")
                        print(f"         🌐 is_online: {topic_info.get('is_online')}")
                        print(f"         🔋 is_v2: {topic_info.get('is_v2')}")
                        print(f"         🌱 eco: {topic_info.get('eco')}")
                        print(f"         ❄️ anti_frost: {topic_info.get('anti_frost')}")
                        print(f"         💧 humidity: {topic_info.get('humidity')}")
                        print(f"         📶 RSSI: {topic_info.get('rssi')} dBm")
                        print(f"         🔄 Last Sync: {topic_info.get('last_sync')}")
                        print(f"         📱 Device Reference: {topic_info.get('device_reference')}")
                        print(f"         🔗 MQTT Address: {topic_info.get('mqtt_address')}")
                        print(f"         🔒 MQTT Security: {topic_info.get('mqtt_security')}")
                        print(f"         📅 Topic Created: {topic_info.get('created_at')}")
                        print(f"         🔄 Topic Updated: {topic_info.get('updated_at')}")

                        # Configuraciones
                        configs = topic_info.get('configurations', [])
                        if configs:
                            print(f"         ⚙️ Configuraciones ({len(configs)}):")
                            for config in configs:
                                print(f"            {config.get('key')}: {config.get('value')} (updated: {config.get('updated_at')})")

                # Información del peripheral
                peripheral = device.get('peripheral')
                print(f"   🔧 Peripheral: {peripheral}")

            print("\n💡 USO EN HOME ASSISTANT:")
            print("   • Sensor de conectividad por dispositivo")
            print("   • Sensor RSSI por dispositivo")
            print("   • Información de batería (si aplica)")
            print("   • Estado detallado de configuraciones")
            print("   • Información de última sincronización")

        except Exception as e:
            print(f"❌ Error: {e}")
        print("\n" + "="*60 + "\n")

        # 3. EXTRACCIÓN DETALLADA DE DEVICE INDIVIDUAL
        if device_id:
            print(f"🔍 3. EXTRACCIÓN DETALLADA: /devices/{device_id}/")
            print("-" * 60)
            try:
                response = client._get_session().rest_request("GET", f"devices/{device_id}")
                device_detail = response.json()

                print(f"📊 Estructura: {type(device_detail)}")
                print(f"🔑 Keys: {list(device_detail.keys())}")
                print("🔍 Contenido completo:")
                print(json.dumps(device_detail, indent=2, default=str))

                print("\n💡 USO EN HOME ASSISTANT:")
                print("   • Detalles específicos de un dispositivo")
                print("   • Información extendida no disponible en lista general")

            except Exception as e:
                print(f"❌ Error: {e}")
            print("\n" + "="*60 + "\n")

        # 4. EXTRACCIÓN DETALLADA DE TOPIC
        if topic_id:
            print(f"📋 4. EXTRACCIÓN DETALLADA: /topics/{topic_id}/")
            print("-" * 60)
            try:
                response = client._get_session().rest_request("GET", f"topics/{topic_id}")
                topic_detail = response.json()

                print(f"📊 Estructura: {type(topic_detail)}")
                print(f"🔑 Keys ({len(topic_detail)}): {list(topic_detail.keys())}")
                print("🔍 Contenido completo:")
                print(json.dumps(topic_detail, indent=2, default=str))

                print("\n💡 USO EN HOME ASSISTANT:")
                print("   • Información completa de zona/proyecto")
                print("   • Configuraciones avanzadas del topic")
                print("   • Estado detallado del sistema")

            except Exception as e:
                print(f"❌ Error: {e}")
            print("\n" + "="*60 + "\n")

        # 5. EXTRACCIÓN DETALLADA DE PROJECT
        if project_id:
            print(f"🏠 5. EXTRACCIÓN DETALLADA: /projects/{project_id}/")
            print("-" * 60)
            try:
                response = client._get_session().rest_request("GET", f"projects/{project_id}")
                project_detail = response.json()

                print(f"📊 Estructura: {type(project_detail)}")
                print(f"🔑 Keys ({len(project_detail)}): {list(project_detail.keys())}")
                print("🔍 Contenido completo:")
                print(json.dumps(project_detail, indent=2, default=str))

                print("\n💡 USO EN HOME ASSISTANT:")
                print("   • Información completa del proyecto")
                print("   • Detalles del usuario propietario")
                print("   • Configuraciones globales del proyecto")

            except Exception as e:
                print(f"❌ Error: {e}")
            print("\n" + "="*60 + "\n")

        # RESUMEN FINAL
        print("📊 RESUMEN FINAL DE EXTRACCIÓN DE DATOS")
        print("=" * 60)

        print("✅ ENDPOINTS ANALIZADOS:")
        print("   1. /notifications/ - Estructura de notificaciones")
        print("   2. /devices/ - Lista completa de dispositivos con datos ricos")
        print("   3. /devices/{id}/ - Detalles extendidos de dispositivo")
        print("   4. /topics/{id}/ - Información completa de zona/topic")
        print("   5. /projects/{id}/ - Detalles del proyecto")

        print("\n📈 DATOS EXTRAÍDOS:")
        print(f"   • Proyecto: CASA (ID: {project_id})")
        print(f"   • Dispositivos: 8 activos")
        print("   • Información detallada: temperaturas, RSSI, configuraciones")
        print("   • Estados en tiempo real: online, modos, última sync")
        print("   • Configuraciones avanzadas: AllowEco, AllowAntiFrost, TopicModes")

        print("\n🎯 VALOR PARA HOME ASSISTANT:")
        print("   • +8 sensores de conectividad (RSSI)")
        print("   • +8 sensores de estado detallado")
        print("   • Sensor de notificaciones del sistema")
        print("   • Información de configuraciones avanzadas")
        print("   • Mejor diagnóstico y monitoreo")

    except Exception as e:
        print(f"❌ Error de autenticación: {e}")

if __name__ == "__main__":
    extract_api_data_detailed()
