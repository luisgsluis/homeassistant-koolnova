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
- `hacs.json` con configuración completa (requerido para HACS)
- Archivos de traducción en `translations/`
- Documentación clara

### Configuración HACS Requerida (`hacs.json`)

El archivo `hacs.json` DEBE contener los siguientes campos:

```json
{
  "name": "Nombre de la integración",
  "homeassistant": "versión mínima compatible",
  "domain": "dominio_de_la_integracion",
  "repository": "https://github.com/usuario/repositorio",
  "zip_release": true,
  "config_flow": true,
  "iot_class": "clase_iot",
  "categories": ["Categoría principal"]
}
```

**Campos críticos**:
- `"domain"`: DEBE coincidir exactamente con el dominio en `manifest.json`
- `"zip_release"`: DEBE ser `true` para releases basados en ZIP
- `"repository"`: URL completa del repositorio GitHub

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

### ⚠️ CRÍTICO: Estructura HACS Compatible

**HACS requiere la estructura estándar de GitHub, NO ZIPs personalizados**

### 📁 Estructura de Directorios Requerida

```
ROOT_REPOSITORIO/
├── custom_components/
│   └── koolnova/          ← Nombre del dominio
│       ├── __init__.py
│       ├── manifest.json  ← Versión DEBE coincidir con el tag
│       ├── climate.py
│       └── ... (todos los archivos de la integración)
├── README.md              ← Documentación en la raíz
└── hacs.json              ← Configuración HACS en la raíz
```

### 🔧 Configuración HACS Requerida (`hacs.json`)

```json
{
  "name": "Nombre de la integración",
  "homeassistant": "versión mínima compatible",
  "domain": "dominio_exacto",      // DEBE coincidir con manifest.json
  "repository": "URL_completa_github",
  "config_flow": true/false,
  "iot_class": "clase_iot",
  "categories": ["Categoría"]
}
```

**❌ NO usar**:
- `"zip_release": true` (HACS usa archivos estándar de GitHub)
- `"filename": "custom.zip"` (No se permiten ZIPs personalizados)

### Pasos para Release HACS Compatible

1. **Desarrollo**: Implementar cambios en rama `main`
2. **Testing**: Verificar funcionamiento en HA
3. **Actualización de JSON**:
   - `manifest.json`: Actualizar `"version"` para que coincida con el tag
   - `hacs.json`: Verificar que `"domain"` coincida con `manifest.json`
4. **Commit**: `git commit -m "Release vX.Y.Z"`
5. **Tag**: `git tag -a vX.Y.Z -m "Release vX.Y.Z"`
6. **Push**: `git push origin main --tags`
7. **Crear Release en GitHub**: Usar la interfaz de GitHub (NO workflows personalizados)
8. **HACS**: Los usuarios pueden actualizar vía HACS

### 🎯 Requisitos Clave HACS

- **Estructura**: GitHub estándar (`repositorio-versión/custom_components/dominio/...`)
- **Archivos obligatorios**:
  - `custom_components/koolnova/manifest.json` (con versión correcta)
  - `hacs.json` (en raíz, con dominio correcto)
  - `README.md` (en raíz)
- **Versiones**: El tag y `manifest.json` DEBEN coincidir exactamente
- **Releases**: Crear releases estándar de GitHub (sin assets personalizados)

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
