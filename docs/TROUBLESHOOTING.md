# Troubleshooting the Koolnova Integration

## 🚨 Resolved Critical Import Conflict

### Previous Symptoms
- `ModuleNotFoundError: No module named 'koolnovaapi'`
- 404 errors on every API call
- Integration failed to load in Home Assistant

### Root Cause
Conflict between the PyPI `koolnova-api` package (with hyphen) and the local module `koolnovaapi` (no hyphen) caused 404 errors.

### Fix
- Removed the conflicting PyPI package.
- Renamed local module to `koolnova_api` (underscore).
- Switched to relative imports (`from .koolnova_api.client import …`).
- Added `__init__.py`.

### Verification
- No errors on load.
- All API operations work.
- Logs show normal coordinator activity.

## Common Errors

### 404/400 API Errors (Missing User‑Agent)
**Symptoms**: Cannot connect; logs show `Not Found` or `Bad Request`.
**Cause**: Requires `User-Agent: Mozilla/5.0`.
**Fix**: Ensure client includes required headers.

### Config‑Flow Errors
- **Authentication failed** – Wrong email/password.
- **No projects found** – User has no active project.

### Coordinator Update Failures
- **Update failed** – Connectivity or API downtime.
- **Unexpected error** – API changed; update integration.

### Entities Unavailable
- **Offline project** (`is_online: false`).
- **Authenticator failure**.

### Control Issues
- **Payloads malformed** or out‑of‑range values.
- **Temperature out of range** – Adjust min/max.

## Advanced Debugging

- Inspect states under `climate.koolnova_*` for useful attributes.
- Test API manually with `curl` using required headers.
- Reset integration: remove & reinstall.

## Support
- **Issues** → https://github.com/luisgsluis/homeassistant‑koolnova/issues
- Include relevant logs.
- Specify HA & integration versions.