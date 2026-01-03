# Proceso de Release Koolnova Integration

## Versionado

Las versiones se gestionan en `manifest.json`

### Esquema de Versionado
- **MAJOR**: Cambios incompatibles en la API o funcionalidad
- **MINOR**: Nuevas funcionalidades compatibles hacia atrás
- **PATCH**: Corrección de bugs y mejoras menores

## Git Tags

Crear tags para cada release:

## Compatible con HACS

La integración es compatible con HACS (Home Assistant Community Store):

- **Tipo**: Integration
- **Método de instalación**: GitHub release
- **URL del repositorio**: https://github.com/luisgsluis/homeassistant-koolnova

### Requisitos para HACS
- `manifest.json` con metadata correcta
- `hacs.json` opcional para configuración adicional
- Archivos de traducción en `translations/`
- Documentación clara

## Changelog

### v1.2.0 (Próxima - Fix Crítico)
- 🚨 **FIX CRÍTICO**: Resuelto conflicto de imports que causaba errores 404
- ✅ Eliminado paquete PyPI conflictivo `koolnova-api`
- ✅ Renombrado módulo local a `koolnova_api` (con guión bajo)
- ✅ Implementados imports relativos para estabilidad
- ✅ Agregado `__init__.py` al directorio del módulo
- 📈 Rendimiento optimizado: Solo código local, sin dependencias externas

### v1.1.0
- Mejora en el polling del coordinator
- Soporte para control global de zonas
- Optimización de mapeos HVAC
- Corrección de errores en actualización de sensores

### v1.0.0
- Versión inicial
- Soporte básico para proyectos y zonas
- Control individual de temperatura y modos

## Proceso de Release

### ⚠️ CRÍTICO: Actualización de Archivos JSON

Antes de crear un release, **DEBES** actualizar los siguientes archivos:

1. **`manifest.json`**:
   - Actualizar el campo `"version"` para que coincida exactamente con el número de versión del tag
   - Ejemplo: `"version": "1.2.1"` para el tag `v1.2.1`

2. **`hacs.json`** (opcional pero recomendado):
   - Verificar que la versión de Home Assistant sea compatible
   - Actualizar si es necesario

### Pasos para Release

1. **Desarrollo**: Implementar cambios en rama `main`
2. **Testing**: Verificar funcionamiento en HA
3. **Actualización de JSON**: Actualizar `manifest.json` con la nueva versión
4. **Commit**: `git commit -m "Release vX.Y.Z"`
5. **Tag**: `git tag -a vX.Y.Z -m "Release vX.Y.Z"`
6. **Push**: `git push origin main --tags`
7. **Crear Release en GitHub**: El workflow automático generará el asset ZIP
8. **HACS**: Los usuarios pueden actualizar vía HACS

### ❌ Error Común: Version Mismatch

**PROBLEMA**: Si `manifest.json` no coincide con el tag, HACS mostrará:
```
Downloading luisgsluis/homeassistant-koolnova with version vX.Y.Z failed with (No content to download)
```

**SOLUCIÓN**: Asegúrate de que:
- El tag sea `v1.2.1`
- `manifest.json` tenga `"version": "1.2.1"`
- Ambos sean idénticos (sin prefijos/sufijos)

## Distribución

- **HACS**: Actualización automática
- **Manual**: Descarga desde releases de GitHub
- **Beta**: Usar rama `dev` para testing
