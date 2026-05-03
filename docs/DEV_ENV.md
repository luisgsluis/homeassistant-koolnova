# Development Environment for the Koolnova Integration

## 🚨 Critical Information for Developers

**BEFORE ANY CODE CHANGE:**  
When you open a chat with Cline (your development assistant), **MUST** automatically read all project documentation to understand the full context. Run this command at the start of each session:

```bash
cline "Read and understand the entire Koolnova project documentation. Pay particular attention to ARCHITECTURE.md, TROUBLESHOOTING.md and DEV_ENV.md for critical development rules."
```

## ⚠️ Critical Development Rules

### 1. Imports – NEVER BREAK
- ✅ **Correct**: `from .koolnova_api.client import …`
- ❌ **Critical error**: `from koolnovaapi.client import …`

### 2. Resolved Architecture
- **Relative imports** are required for absolute stability.

### 3. Mandatory Testing
- Clear Python cache after any import changes.
- Verify logs contain no errors before committing.
- Test the integration via the Home Assistant UI.

## 📋 Developer Checklist

Before any change:
- [ ] Read `ARCHITECTURE.md` completely.
- [ ] Verify import rules are followed.
- [ ] Clear Python cache (`find . -type d -name __pycache__ -exec rm -r {} +`).
- [ ] Test the integration after any change.
- [ ] Update documentation if behavior changes.

**Remember**: Project stability depends on strict adherence to these rules.

## ⚠️ Import Architecture (Re‑emphasized)

### Critical Change in Development
- **Before**: Local module named `koolnovaapi` (no hyphen).
- **Now**: Local module renamed to `koolnova_api` (underscore).
- **Imports**: Always use relative imports `from .koolnova_api.client import …`.
- **Never use**: Absolute imports like `from koolnovaapi.client import …`.

### Why this change?
Resolved a critical conflict between:
- PyPI package `koolnova-api` (caused 404 errors).
- Local module `koolnovaapi` (source code).

### Golden Rule in Development
🔴 **ALWAYS clear Python cache** after any import changes.

## VS Code Remote‑SSH Setup
1. Development folder locally at `$HOME/homeassistant/config/custom_components/koolnova`.

## Using Cline
Cline is a development helper that runs commands inside the container. To use Cline:
- Run commands in the integrated terminal.
- Edit files directly.
- Manage version control with Git.

## Development Path
The integration is developed at:
```bash
$HOME/docker/homeassistant/config/custom_components/koolnova
```

## Restart Home Assistant
After code changes, restart Home Assistant to load the new code:
```bash
docker restart homeassistant
```

## Pre‑Push Testing
Before pushing to GitHub, always test the integration:
1. Restart HA: `docker restart homeassistant`
2. Check logs for errors: `docker logs homeassistant`
3. Tail detailed logs: `tail -f $HOME/docker/homeassistant/config/home-assistant.log`
4. Verify configuration via the HA UI.
5. Confirm entities work correctly.
Use Chrome locally to access HA during testing.

## Project Structure
- `koolnova_api/` – API client (contains `__init__.py` to make it a valid package).
- `__init__.py` – Integration initialization.
- `coordinator.py` – Data coordinator.
- `climate.py` – Climate entities.
- `config_flow.py` – Configuration flow.
- `const.py` – Constants and mappings.
- `docs/` – Documentation.