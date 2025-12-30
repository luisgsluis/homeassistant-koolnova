# Entorno de Desarrollo Koolnova Integration

## Configuración VS Code Remote SSH

1. Instala la extensión "Remote SSH" en VS Code
2. Conecta a tu Raspberry Pi vía SSH
3. Abre la carpeta del proyecto: `/home/admin/docker/homeassistant/config/custom_components/koolnova`

## Uso de Cline

Cline es una herramienta de desarrollo que facilita la gestión del código. Para usar Cline:

- Ejecuta comandos en la terminal integrada
- Realiza cambios en archivos directamente
- Gestiona el control de versiones con Git

## Ruta de Desarrollo

La integración se desarrolla en:
```
/home/admin/docker/homeassistant/config/custom_components/koolnova
```

## Reinicio de Home Assistant

Después de realizar cambios en el código, reinicia Home Assistant para que tome los cambios:

```bash
docker restart homeassistant
```

## Estructura del Proyecto

- `koolnovaapi/`: Cliente API para Koolnova
- `__init__.py`: Inicialización de la integración
- `coordinator.py`: Coordinador de datos
- `climate.py`: Entidades climáticas
- `config_flow.py`: Flujo de configuración
- `const.py`: Constantes y mapeos
- `docs/`: Documentación
