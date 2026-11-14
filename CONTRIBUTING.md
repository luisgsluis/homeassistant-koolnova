# Contributing to Koolnova for Home Assistant

Thanks for wanting to help. This is a custom HACS integration that talks to
the Koolnova cloud API — which is undocumented, brittle, and bans your IP if
you push it. Read `docs/API.md` before touching the client.

## Getting started

The integration lives in `custom_components/koolnova/` and must keep the
standard HACS shape: `custom_components/koolnova/`, `hacs.json` and
`README.md` at the repo root, no zips, no `zip_release`.

Run the client tests (stdlib `unittest`, no pytest, no HA install):

```bash
python3 -m unittest discover -s tests -t . -v
```

Every HTTP call is mocked. **Never put real credentials, tokens or hostnames in the tests.**

## Rules that come from the API

- Koolnova bans your IP when polled too often and on repeated failed logins: never lower
  `MIN_UPDATE_INTERVAL` or `AUTH_FAILURE_COOLDOWN` (see `docs/API.md`, `docs/DEVELOPMENT.md`).
- The API needs browser-like headers on every request (`User-Agent`, `origin`,
  `referer`). Missing them produces 400/404s that look like auth failures.
- `koolnova_api/` is vendored on purpose: relative imports only (import rule in
  `docs/DEVELOPMENT.md`).

## Conventions

- Home Assistant-side code follows the HA developer guidelines. Translations
  go in `strings.json` and `translations/` (en, es, it).
- Version changes and releases: `docs/DEVELOPMENT.md` → "Publishing a release" (the git tag and
  the manifest version must match exactly).
- Update `docs/` (`API.md`, `DEVELOPMENT.md`, `TROUBLESHOOTING.md`) when
  behavior changes.

## Testing changes

The vendored client is covered by the unit tests; the sensor and climate platforms by tests that
need Home Assistant installed. `config_flow.py` and the rest of the HA side only mean something
against a live HA instance and a real Koolnova account: if you changed it, say what you tested on
the PR.

## Issues and discussions

- Bugs → use the bug report template.
- Feature ideas → the feature request template.
- Questions → GitHub Discussions.
- Security problems → report privately via **Security → Report a
  vulnerability** (see [SECURITY.md](SECURITY.md)). Please don't open a public
  issue.
