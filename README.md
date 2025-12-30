# Koolnova Home Assistant Integration

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-41BDF5.svg)](https://github.com/hacs/integration)

Integración personalizada para Home Assistant que permite controlar sistemas HVAC Koolnova a través de su API REST.

## 🚨 Información Crítica para Desarrolladores

**ANTES DE CUALQUIER CAMBIO EN EL CÓDIGO:**

Cuando abras un chat con Cline (tu asistente de desarrollo), **DEBE** leer automáticamente toda la documentación del proyecto para entender el contexto completo. Ejecuta este comando al inicio de cada sesión:

```bash
cline "Lee y comprende toda la documentación del proyecto Koolnova. Revisa especialmente ARCHITECTURE.md, TROUBLESHOUTING.md y DEV_ENV.md para entender las reglas críticas de desarrollo."
```

### Documentación Esencial
- **[ARCHITECTURE.md](docs/ARCHITECTURE.md)** - Arquitectura y reglas de imports
- **[TROUBLESHOUTING.md](docs/TROUBLESHOUTING.md)** - Problemas comunes y soluciones
- **[DEV_ENV.md](docs/DEV_ENV.md)** - Reglas críticas de desarrollo
- **[API.md](docs/API.md)** - Documentación de la API de Koolnova
- **[RELEASE.md](docs/RELEASE.md)** - Historial de versiones

## ⚠️ Reglas Críticas de Desarrollo

### 1. Imports - NUNCA VIOLAR
- ✅ **CORRECTO**: `from .koolnova_api.client import ...`
- ❌ **ERROR CRÍTICO**: `from koolnovaapi.client import ...`
- ❌ **ERROR CRÍTICO**: Instalar paquetes PyPI externos

### 2. Arquitectura Resuelta
- **Módulo local**: `koolnova_api/` (con guión bajo)
- **Paquete PyPI eliminado**: Conflicto resuelto
- **Imports relativos**: Para estabilidad absoluta

### 3. Testing Obligatorio
- Limpiar caché Python después de cambios en imports
- Verificar logs sin errores antes de commits
- Probar configuración desde UI de HA

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
3. Instalar y reiniciar HA

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

## Arquitectura Técnica

### Polling Inteligente
- **Setup inicial**: Carga proyectos + sensores
- **Actualizaciones**: Solo sensores (proyectos cacheados)
- **Optimización**: Reduce carga en API

### Estructura de Entidades
- `climate.koolnova_*` - Entidades de zonas
- `climate.koolnova_project_*` - Control global

### Cliente API Local
- Módulo `koolnova_api/` con autenticación automática
- Headers específicos para API de Koolnova
- Manejo robusto de errores y reconexiones

## Logs y Debugging

```bash
# Ver logs en tiempo real
docker logs -f homeassistant

# Buscar errores específicos
docker logs homeassistant | grep koolnova
```

### Mensajes Importantes
- `"Fetching sensors data from Koolnova API (periodic update)"` - Polling normal
- `"Using optimized polling: sensors only"` - Optimización funcionando
- `"Setup failed for custom integration 'koolnova'"` - Error de carga

## Solución de Problemas

Ver **[TROUBLESHOOTING.md](docs/TROUBLESHOUTING.md)** para problemas comunes.

### Problemas Frecuentes
1. **Error 404**: Conflicto de paquetes - verificar imports
2. **Entidades unavailable**: Proyecto offline
3. **Cambios no aplican**: Verificar rangos de temperatura

## Desarrollo

Ver **[DEV_ENV.md](docs/DEV_ENV.md)** para configuración del entorno de desarrollo.

### Comandos Útiles
```bash
# Limpiar caché Python
find . -name "*.pyc" -delete && find . -name "__pycache__" -delete

# Reiniciar HA
docker restart homeassistant

# Ver logs detallados
tail -f /config/home-assistant.log
```

## Contribución

1. Leer toda la documentación antes de cambios
2. Seguir reglas de imports estrictamente
3. Probar exhaustivamente antes de commits
4. Actualizar documentación según cambios

## Soporte

- **Issues**: [GitHub Issues](https://github.com/luisgsluis/ha-koolnova/issues)
- **Documentación**: [docs/](docs/) folder
- **Licencia**: MIT

---

## 📋 Checklist para Desarrolladores

Antes de cualquier cambio:
- [ ] Leer ARCHITECTURE.md completamente
- [ ] Verificar reglas de imports
- [ ] Limpiar caché Python
- [ ] Probar integración después de cambios
- [ ] Actualizar documentación si aplica

**Recuerda**: La estabilidad del proyecto depende del cumplimiento estricto de estas reglas.</content>
