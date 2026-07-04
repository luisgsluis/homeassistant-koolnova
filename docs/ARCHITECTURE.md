# Arquitectura de la Integración Koolnova

La integración Koolnova para Home Assistant está estructurada como una integración custom que consume la API REST de Koolnova para controlar sistemas HVAC.

## Cliente API vendorizado (regla de imports)

El cliente REST (`koolnova_api/`) es un **fork local** de `koolnova-api` — todo el crédito al
desarrollador original. Se distribuye dentro del repositorio, no como dependencia PyPI, para evitar
un conflicto que provocaba errores 404: el paquete PyPI `koolnova-api` (con guión) colisionaba con el
módulo local, que antes se llamaba `koolnovaapi` (sin guión).

Reglas resultantes:
- El módulo local se llama `koolnova_api` (con guión bajo) y contiene `__init__.py`.
- Se importa **siempre** con imports relativos: `from .koolnova_api.client import ...`.
- No añadir `koolnova-api` como dependencia en `manifest.json`.

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
