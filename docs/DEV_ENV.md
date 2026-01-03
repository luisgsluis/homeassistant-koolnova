# Entorno de Desarrollo Koolnova Integration

## ⚠️ Importante: Arquitectura de Imports

### Cambio Crítico en Desarrollo
- **Antes**: Módulo local se llamaba `koolnovaapi` (sin guión)
- **Ahora**: Módulo local se llama `koolnova_api` (con guión bajo)
- **Imports**: Usar siempre imports relativos `from .koolnova_api.client import ...`
- **Nunca usar**: Imports absolutos como `from koolnovaapi.client import ...`

### ¿Por qué este cambio?
Resolvió conflicto crítico entre:
- Paquete PyPI `koolnova-api` (causaba errores 404)
- Módulo local `koolnovaapi` (código fuente)

### Regla de Oro en Desarrollo
🔴 **SIEMPRE limpiar caché Python** después de cambios en imports

---

## Configuración VS Code Remote SSH

1. Carpeta de proyecto desarrollo en local con docker  `$HOME/homeassistant/config/custom_components/koolnova`

## Uso de Cline

Cline es una herramienta de desarrollo que facilita la gestión del código. Para usar Cline:

- Ejecuta comandos en la terminal integrada
- Realiza cambios en archivos directamente
- Gestiona el control de versiones con Git

## Ruta de Desarrollo

La integración se desarrolla en:
```
$HOME/docker/homeassistant/config/custom_components/koolnova
```

## Reinicio de Home Assistant

Después de realizar cambios en el código, reinicia Home Assistant para que tome los cambios:

```bash
docker restart homeassistant
```

## Testing antes de Push

Antes de hacer push a GitHub, siempre prueba la integración:

1. Reinicia HA con `docker restart homeassistant`
2. Verifica que no hay errores en logs: `docker logs homeassistant`
3. Revisa logs detallados: `tail -f $HOME/docker/homeassistant/config/home-assistant.log`
4. Prueba la configuración desde la UI de HA
5. Verifica que las entidades funcionan correctamente

Usa Chrome en local para acceder a HA durante las pruebas.

## Estructura del Proyecto

- `koolnova_api/`: Cliente API para Koolnova (con __init__.py para paquete válido)
- `__init__.py`: Inicialización de la integración
- `coordinator.py`: Coordinador de datos
- `climate.py`: Entidades climáticas
- `config_flow.py`: Flujo de configuración
- `const.py`: Constantes y mapeos
- `docs/`: Documentación
