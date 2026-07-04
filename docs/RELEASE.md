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

> La configuración detallada de `hacs.json` y la estructura de directorios que exige HACS está en
> la sección [Proceso de Release](#proceso-de-release) más abajo.

## Changelog

### v1.3.0
- 🚨 **FIX (issue #4)**: Autenticación fallaba con 404 en `/auth/v2/login/`. Koolnova cambió su API
  (mayo 2026): ahora exige User-Agent Chrome moderno, headers `sec-ch-ua`/`sec-fetch-*` y el login
  en el campo `username` del payload (no `email`).
- 🛡️ **Anti-ban**: Koolnova banea IPs automáticamente si se consulta más de 1 vez cada 30 s
  (confirmado por su soporte). Intervalo por defecto y mínimo subidos a 30 s, con clamp en el
  coordinator para configuraciones antiguas.
- 🛡️ **Anti-ban**: cooldown de 5 min tras un fallo de login antes de reintentar (los logins
  fallidos repetidos también provocan ban de IP).
- 🔒 Ya no se registra en logs de debug el payload de login (contenía la contraseña) ni el token.
- 🧹 Eliminado código muerto heredado del fork original (métodos de piscinas/hubs, ~110 líneas) y
  dependencia implícita de `dateutil`; User-Agent unificado en una sola constante.
- 🔧 **HACS**: corregido `hacs.json` (quitadas claves no admitidas que hacían fallar el check
  `hacsjson`); el workflow de validación ahora pasa (`brands` se ignora por ser repo custom).
- Los modos HVAC por defecto **no cambian**.

### v1.2.6
- 🔒 **Seguridad**: Eliminado `tests/` del repositorio y purgado del historial de git (contenía
  scripts de exploración de API con credenciales en texto plano). Historial de commits reescrito.
- 🧹 Estructura del repositorio limpiada y documentada (`CLAUDE.md` añadido)
- ✅ Añadido workflow de validación HACS/hassfest (`.github/workflows/validate.yml`)
- 📝 Corregido enlace roto a `TROUBLESHOOTING.md` en el README

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

### 🔧 Configuración HACS (`hacs.json`)

`hacs.json` solo admite un conjunto reducido de claves. Metadatos como `domain`, `config_flow`,
`iot_class`, `categories` o `repository` van en `manifest.json`, **no aquí** — si se ponen en
`hacs.json`, el check `hacsjson` del workflow falla con "extra keys not allowed".

```json
{
  "name": "Koolnova",
  "homeassistant": "2025.12.0",
  "render_readme": true,
  "country": ["ES"],
  "hide_default_branch": false
}
```

**❌ NO usar en `hacs.json`**:
- `domain`, `config_flow`, `iot_class`, `categories`, `repository` (van en `manifest.json`)
- `zip_release` / `filename` (HACS usa archivos estándar de GitHub, no ZIPs personalizados)

### Pasos para Release HACS Compatible

1. **Desarrollo**: Implementar cambios en rama `main`
2. **Testing**: Verificar funcionamiento en HA
3. **Actualización de JSON**:
   - `manifest.json`: Actualizar `"version"` para que coincida con el tag
4. **Commit**: `git commit -m "Release vX.Y.Z"`
5. **Tag**: `git tag -a vX.Y.Z -m "Release vX.Y.Z"`
6. **Push**: `git push origin main --tags`
7. **Crear Release en GitHub**: Usar la interfaz de GitHub (NO workflows personalizados)
8. **HACS**: Los usuarios pueden actualizar vía HACS

### 🎯 Requisitos Clave HACS

- **Estructura**: GitHub estándar (`repositorio-versión/custom_components/dominio/...`)
- **Archivos obligatorios**:
  - `custom_components/koolnova/manifest.json` (con versión correcta)
  - `hacs.json` (en raíz, solo con las claves admitidas)
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
