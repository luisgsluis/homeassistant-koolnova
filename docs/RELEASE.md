# Proceso de Release Koolnova Integration

## Versionado

Las versiones se gestionan en `manifest.json`:

```json
{
  "version": "1.1.0"
}
```

### Esquema de Versionado
- **MAJOR**: Cambios incompatibles en la API o funcionalidad
- **MINOR**: Nuevas funcionalidades compatibles hacia atrás
- **PATCH**: Corrección de bugs y mejoras menores

## Git Tags

Crear tags para cada release:

```bash
git tag -a v1.1.0 -m "Release v1.1.0: Descripción de cambios"
git push origin v1.1.0
```

## Compatible con HACS

La integración es compatible con HACS (Home Assistant Community Store):

- **Tipo**: Integration
- **Método de instalación**: GitHub release
- **URL del repositorio**: https://github.com/luisgsluis/ha-koolnova

### Requisitos para HACS
- `manifest.json` con metadata correcta
- `hacs.json` opcional para configuración adicional
- Archivos de traducción en `translations/`
- Documentación clara

## Changelog

### v1.1.0 (Actual)
- Mejora en el polling del coordinator
- Soporte para control global de zonas
- Optimización de mapeos HVAC
- Corrección de errores en actualización de sensores

### v1.0.0
- Versión inicial
- Soporte básico para proyectos y zonas
- Control individual de temperatura y modos

## Proceso de Release

1. **Desarrollo**: Implementar cambios en rama `main`
2. **Testing**: Verificar funcionamiento en HA
3. **Versionado**: Actualizar versión en `manifest.json`
4. **Commit**: `git commit -m "Release vX.Y.Z"`
5. **Tag**: `git tag -a vX.Y.Z`
6. **Push**: `git push origin main --tags`
7. **HACS**: Los usuarios pueden actualizar vía HACS

## Distribución

- **HACS**: Actualización automática
- **Manual**: Descarga desde releases de GitHub
- **Beta**: Usar rama `dev` para testing
