# Entorno de Desarrollo

Guía para desarrollar y probar la integración Koolnova.

## Regla crítica: imports del cliente API

El cliente API vive en `custom_components/koolnova/koolnova_api/` y **siempre** se importa con
imports relativos:

```python
from .koolnova_api.client import KoolnovaAPIRestClient   # ✅ correcto
from koolnovaapi.client import KoolnovaAPIRestClient      # ❌ rompe la integración
```

El módulo se llama `koolnova_api` (con guión bajo). El nombre antiguo `koolnovaapi` (sin guión)
colisionaba con el paquete PyPI `koolnova-api` y provocaba errores 404. Tras cualquier cambio en
imports, **limpia la caché de Python** antes de probar. Detalle completo en
[ARCHITECTURE.md](ARCHITECTURE.md) y [TROUBLESHOOTING.md](TROUBLESHOOTING.md).

## Entorno de pruebas

El desarrollo se hace contra una instancia local de Home Assistant en Docker. La integración se
edita directamente en el directorio de configuración de HA:

```
$HOME/docker/homeassistant/config/custom_components/koolnova
```

Tras cada cambio, reinicia HA para que lo tome:

```bash
docker restart homeassistant
```

## Checklist antes de hacer push

1. `docker restart homeassistant`
2. Comprobar que no hay errores en logs:
   - `docker logs homeassistant`
   - `tail -f $HOME/docker/homeassistant/config/home-assistant.log`
3. Probar la configuración desde la UI de Home Assistant.
4. Verificar que las entidades `climate.koolnova_*` funcionan (temperatura, modo, ventilador).
