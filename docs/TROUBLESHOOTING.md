# Troubleshooting Koolnova Integration

## 🚨 Problema Crítico Resuelto: Conflicto de Imports

### Síntomas Anteriores
- Error: `ModuleNotFoundError: No module named 'koolnovaapi'`
- Error 404 en todas las operaciones API
- Integración no carga en Home Assistant

### Causa Raíz
Conflicto entre:
- **Paquete PyPI**: `koolnova-api` (con guión) - causaba errores 404
- **Módulo local**: `koolnovaapi` (sin guión) - código fuente

### Solución Aplicada
✅ **Eliminado paquete PyPI conflictivo**
✅ **Renombrado módulo local** a `koolnova_api`
✅ **Implementados imports relativos** (`from .koolnova_api.client import ...`)
✅ **Agregado `__init__.py`** al directorio del módulo

### Verificación
- Integración carga sin errores
- Todas las operaciones API funcionan correctamente
- Logs muestran actividad normal del coordinator

---

## Logs de Home Assistant

Para ver los logs de HA y la integración:

```bash
docker logs homeassistant
```

O en tiempo real:

```bash
docker logs -f homeassistant
```

También puedes revisar el archivo de logs principal:

```bash
tail -f /home/admin/docker/homeassistant/config/home-assistant.log
```

## Errores Comunes

### Error 404/400 en API (Falta User-Agent)

**Síntomas**:
- Integración no puede conectarse
- Errores "Not Found" o "Bad Request" en logs

**Causa**:
- La API requiere header `User-Agent: Mozilla/5.0`
- Headers incompletos en requests

**Solución**:
- Verificar que el cliente API incluye todos los headers requeridos
- Revisar `koolnova_api/client.py` para configuración de headers

### Config Flow Errors

**Error**: "Authentication failed"
- **Causa**: Credenciales incorrectas
- **Solución**: Verificar email/contraseña en app Koolnova

**Error**: "No projects found"
- **Causa**: Usuario sin proyectos activos
- **Solución**: Crear proyecto en app Koolnova

### Coordinator Update Failures

**Error**: "Update failed" en logs
- **Causa**: Problemas de conectividad o API temporalmente down
- **Solución**: Verificar conexión a internet y estado de app Koolnova

**Error**: "Unexpected error"
- **Causa**: Cambios en API de Koolnova
- **Solución**: Verificar compatibilidad de versión

### Entidades No Disponibles

**Síntomas**:
- Entidades climate aparecen como "unavailable"

**Causas posibles**:
- Proyecto offline (`is_online: false`)
- Coordinator no actualiza datos
- Problemas de autenticación

**Solución**:
- Verificar estado del proyecto en app Koolnova
- Reiniciar HA: `docker restart homeassistant`
- Reconfigurar integración

### Problemas de Control

**Error**: Cambios no se aplican
- **Causa**: Payloads incorrectos o límites excedidos
- **Solución**: Verificar rangos de temperatura y códigos válidos

**Error**: "Temperature out of range"
- **Causa**: Temperatura fuera de límites configurados
- **Solución**: Ajustar `min_temp`/`max_temp` en opciones

## Debugging Avanzado

### Verificar Datos del Coordinator

En Developer Tools > States, buscar entidades `climate.koolnova_*`

Atributos útiles:
- `online_status`
- `last_sync`
- `total_zones`

### Test Manual de API

Usar curl para probar endpoints:

```bash
curl -H "User-Agent: Mozilla/5.0" \
     -H "Authorization: Bearer YOUR_TOKEN" \
     https://api.koolnova.com/projects/
```

### Reset de Integración

1. Remover integración en HA UI
2. Reiniciar HA
3. Reinstalar integración
4. Reconfigurar con credenciales

## Contacto y Soporte

- **Issues**: https://github.com/luisgsluis/ha-koolnova/issues
- **Logs**: Incluir logs relevantes al reportar bugs
- **Versión**: Especificar versión de HA y integración
