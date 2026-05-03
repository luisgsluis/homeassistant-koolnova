# Koolnova Integration Release Process

## Versioning

Versions are managed in `manifest.json`.

### Version Scheme
- **MAJOR**: Incompatible API or feature changes
- **MINOR**: Backward-compatible new features
- **PATCH**: Bug fixes and minor improvements

## Git Tags

Create tags for each release following semantic versioning.

## HACS Compatibility

This integration is HACS (Home Assistant Community Store) compatible:

- **Type**: Integration
- **Installation method**: GitHub release (standard GitHub releases)
- **Repository URL**: https://github.com/luisgsluis/homeassistant-koolnova

### HACS Requirements
- `manifest.json` with correct metadata
- `hacs.json` with complete configuration
- Translation files in `translations/` (optional)
- Clear documentation

### Required HACS Configuration (`hacs.json`)

The `hacs.json` file MUST include the following fields:

```json
{
  "name": "Integration Name",
  "homeassistant": "minimum compatible version",
  "domain": "integration_domain",
  "repository": "https://github.com/user/repository",
  "zip_release": false,
  "config_flow": true,
  "iot_class": "iot_class",
  "categories": ["Category"]
}
```

**Critical fields**:
- `"domain"`: MUST match `manifest.json` domain exactly
- `"repository"`: Full GitHub repository URL
- `"zip_release"`: `false` (HACS uses standard GitHub zip downloads)

## Changelog

### v1.2.0 (Upcoming – Critical Fix)
- 🚨 **CRITICAL FIX**: Resolved import conflict that caused 404 errors
- ✅ Removed conflicting PyPI package `koolnova-api`
- ✅ Renamed local module to `koolnova_api` (underscore)
- ✅ Implemented relative imports for stability
- ✅ Added `__init__.py` to module directory
- 📈 Performance optimized: local code only, no external dependencies

### v1.1.0
- Improved coordinator polling
- Global zone control support
- HVAC mapping optimizations
- Sensor update bug fixes

### v1.0.0
- Initial release
- Basic project and zone support
- Individual temperature and mode control

## Release Process

### ⚠️ CRITICAL: HACS-Compatible Structure

**HACS requires standard GitHub structure, NOT custom ZIPs**

### 📁 Required Directory Structure

```
REPOSITORY_ROOT/
├── custom_components/
│   └── koolnova/          ← Domain name
│       ├── __init__.py
│       ├── manifest.json  ← Version MUST match tag
│       ├── climate.py
│       └── ... (all integration files)
├── README.md              ← Root documentation
└── hacs.json              ← HACS config in root
```

### 🔧 Required HACS Configuration (`hacs.json`)

```json
{
  "name": "Integration Name",
  "homeassistant": "minimum version",
  "domain": "exact_domain",      // MUST match manifest.json
  "repository": "full_github_url",
  "config_flow": true/false,
  "iot_class": "iot_class",
  "categories": ["Category"]
}
```

**❌ DO NOT USE**:
- `"zip_release": true` (HACS uses standard GitHub downloads)
- `"filename": "custom.zip"` (no custom ZIPs allowed)

### Steps for HACS-Compatible Release

1. **Development**: Implement changes in a feature branch
2. **Testing**: Verify functionality in Home Assistant
3. **Update JSON files**:
   - `manifest.json`: Set `"version"` to match upcoming tag (e.g., `v1.2.1` → `"version": "1.2.1"`)
   - `hacs.json`: Verify `"domain"` matches `manifest.json`
4. **Commit**: `git commit -m "Release vX.Y.Z"`
5. **Tag**: `git tag -a vX.Y.Z -m "Release vX.Y.Z"`
6. **Push**: `git push origin main --tags`
7. **Create GitHub Release**: Use GitHub UI (no custom workflows needed)
8. **HACS**: Users can now update via HACS

### 🎯 Key HACS Requirements

- **Structure**: Standard GitHub (`repository-version/custom_components/domain/...`)
- **Required files**:
  - `custom_components/koolnova/manifest.json` (correct version)
  - `hacs.json` (correct domain in root)
  - `README.md` (root documentation)
- **Versions**: Tag and `manifest.json` MUST be identical
- **Releases**: Standard GitHub releases (no custom assets)

### ❌ Common Error: Version Mismatch

**PROBLEM**: If `manifest.json` does not match the tag, HACS shows:
```
Downloading luisgsluis/homeassistant-koolnova with version vX.Y.Z failed with (No content to download)
```

**SOLUTION**: Ensure that:
- Tag is `v1.2.1`
- `manifest.json` has `"version": "1.2.1"`
- They are exactly identical (no prefix/suffix)

## Distribution

- **HACS**: Automatic updates
- **Manual**: Download from GitHub releases
- **Beta**: Use `dev` branch for testing

## Pre-Release Checklist

- [ ] All changes tested in Home Assistant
- [ ] `manifest.json` version matches upcoming tag
- [ ] `hacs.json` configured correctly
- [ ] `custom_components/` directory present
- [ ] All imports use relative syntax (development rule check)
- [ ] No PyPI dependencies except HA core
- [ ] Documentation updated
- [ ] CHANGELOG entry added