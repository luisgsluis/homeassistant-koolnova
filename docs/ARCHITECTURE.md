# Arquitectura de la Integración Koolnova

La integración Koolnova para Home Assistant está estructurada como una integración custom que consume la API REST de Koolnova para controlar sistemas HVAC.

## ⚠️ Importante: Arquitectura de Imports Resuelta

### Problema Original
La integración sufrió un conflicto crítico de imports entre:
- **Paquete PyPI**: `koolnova-api` (con guión) - distribución externa instalada
- **Módulo local**: `koolnovaapi` (sin guión) - código fuente local

### Solución Implementada
- **Eliminado paquete PyPI conflictivo** que causaba errores 404
- **Renombrado módulo local** a `koolnova_api` (con guión bajo)
- **Implementados imports relativos** para evitar conflictos con paquetes globales
- **Agregado `__init__.py`** para convertir directorio en paquete Python válido

### Beneficios
- ✅ **Sin dependencias externas**: Solo usa código local
- ✅ **Imports estables**: No hay conflictos con paquetes PyPI
- ✅ **Mantenimiento simplificado**: Todo el código está bajo control local
- ✅ **Rendimiento optimizado**: Sin sobrecarga de paquetes externos

## Estructura de Archivos

### `__init__.py`
- **Función**: Setup y unload de la integración
- **Responsabilidades**:
  - Registro de plataformas
  - Configuración del coordinator
  - Manejo del ciclo de vida de la integración

### `coordinator.py`
- **Función**: DataUpdateCoordinator para polling de la API
- **Responsabilidades**:
  - Polling periódico de datos de proyectos y sensores
  - Actualización de datos en caché
  - Manejo de errores de conexión
  - Métodos para actualizar sensores y proyectos

### `climate.py`
- **Función**: Entidades HVAC (zonas y proyecto global)
- **Responsabilidades**:
  - `KoolnovaProjectEntity`: Control global del proyecto (modo HVAC, temperatura global, velocidad de ventilador global)
  - `KoolnovaZoneEntity`: Control individual de cada zona/sensor
  - Mapeo entre modos HA y códigos Koolnova
  - Validación de rangos de temperatura

### `config_flow.py`
- **Función**: Flujo de configuración UI
- **Responsabilidades**:
  - Formulario de configuración inicial
  - Validación de credenciales
  - Opciones de configuración avanzada (intervalos, modos, rangos)

### `const.py`
- **Función**: Constantes y mapeos
- **Responsabilidades**:
  - Definición de constantes de configuración
  - Mapeos entre códigos Koolnova y modos HA:
    - `KOOLNOVA_TO_HVAC_MODE`: Modos del proyecto
    - `KOOLNOVA_ZONE_STATUS_TO_HVAC`: Estados de las zonas
    - `KOOLNOVA_TO_FAN`: Velocidades de ventilador

## Arquitectura del Cliente API

### `koolnova_api/`
- **`client.py`**: Cliente principal para llamadas a la API
- **`session.py`**: Manejo de autenticación y sesiones
- **`exceptions.py`**: Excepciones personalizadas
- **`const.py`**: Constantes de la API
- **`__init__.py`**: Convierte directorio en paquete Python válido

## Flujo de Datos

1. **Configuración**: El usuario configura credenciales vía config_flow
2. **Polling**: Coordinator obtiene proyectos y sensores periódicamente
3. **Entidades**: Se crean entidades climate para proyecto y zonas
4. **Control**: Los cambios se envían vía API y se actualiza la caché local

## Dependencias

- Home Assistant Core
- Librerías estándar de Python
- Cliente API personalizado para Koolnova
