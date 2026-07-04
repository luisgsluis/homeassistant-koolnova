# Koolnova Home Assistant Integration

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-41BDF5.svg)](https://github.com/hacs/integration)

Integración personalizada para Home Assistant que permite controlar sistemas HVAC Koolnova a través de su API REST.

## 📋 Documentación Completa

Para desarrolladores y usuarios avanzados, consulta la documentación detallada:

- **[ARCHITECTURE.md](docs/ARCHITECTURE.md)** - Arquitectura y reglas de imports
- **[TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md)** - Problemas comunes y soluciones
- **[DEV_ENV.md](docs/DEV_ENV.md)** - Configuración del entorno de desarrollo
- **[API.md](docs/API.md)** - Documentación de la API de Koolnova
- **[RELEASE.md](docs/RELEASE.md)** - Historial de versiones y proceso de release

## Características

- 🌡️ Control individual de temperatura por zona
- ❄️ Control de modos HVAC (COOL/HEAT/AUTO/OFF)
- 🌬️ Control de velocidad de ventiladores
- 🏠 Control global del proyecto
- 🔄 Polling inteligente (sensores cada minuto, proyectos cacheados)
- 🎛️ Configuración avanzada vía UI

## Instalación

### HACS (Recomendado)
1. Agregar este repositorio como integración custom en HACS
2. Buscar "Koolnova" en la tienda
3. Instalar y reiniciar Home Assistant

### Manual
1. Copiar `custom_components/koolnova/` a tu directorio de configuraciones
2. Reiniciar Home Assistant
3. Configurar vía UI

## Configuración

1. Ir a **Configuración** → **Dispositivos y Servicios** → **Agregar Integración**
2. Buscar **"Koolnova"**
3. Ingresar credenciales de la app Koolnova
4. Configurar opciones avanzadas (opcional)

### Opciones Disponibles
- **Intervalo de actualización**: 30-3600 segundos
- **Modos HVAC del proyecto**: Seleccionar modos disponibles
- **Modos HVAC de zonas**: Seleccionar modos por zona
- **Rango de temperatura**: Mín/Máx configurables

## Soporte

- **Issues**: [GitHub Issues](https://github.com/luisgsluis/homeassistant-koolnova/issues)
- **Documentación**: [docs/](docs/) folder
- **Licencia**: MIT

