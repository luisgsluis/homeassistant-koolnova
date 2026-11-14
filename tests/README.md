# Tests

Tests for the vendored `koolnova_api` client. They run on the standard library alone
(`unittest` + `unittest.mock`) and need neither pytest nor a Home Assistant install:

```bash
python3 -m unittest discover -s tests -t . -v
```

**Every HTTP call is mocked. Never put real credentials, tokens or hostnames in here**.

These cover the parts that have actually broken in production:

| File | Guards against |
|---|---|
| `test_session.py` | the login payload field (`email`, not `username`) and the browser headers, i.e. a login regression and the 404s from missing headers |
| `test_client.py` | HTTP verbs and paths per endpoint (`PUT` for sensors, `PATCH` for topics), response parsing, and the auth-failure cooldown that prevents IP bans |
| `test_const.py` | the mode/status/fan code tables and their auto-generated inverses |
| `test_integration.py` | login, 401 refresh and retries over a real socket against a local `http.server` |
| `test_translations.py` | translation files and the attribute keys they describe (technical keys, display text in the translations) |
| `test_sensor.py`, `test_climate.py` | the sensor and climate platforms; need Home Assistant installed, otherwise they skip |

The rest of the HA side (e.g. `config_flow.py`) is not covered: it needs a running Home Assistant to be meaningful. How to run the HA-dependent tests: [../docs/DEVELOPMENT.md](../docs/DEVELOPMENT.md).
