# The Koolnova API

Reference for the REST API this integration consumes. **It is neither public nor documented**:
everything here was reverse-engineered from the `app.koolnova.com` webapp and verified against the
client code in `custom_components/koolnova/koolnova_api/`.

Base: `https://api.koolnova.com` (Django REST framework).

> If you change the client, update this document in the same commit. It is the only description of
> this API that exists.

## Rules that break everything when ignored

1. **Browser-like headers on every request.** Since May 2026 the API answers `404` (not `401`, not
   `403`) to requests without them, which makes it look like the endpoint is gone. See
   `COMMON_HEADERS` in `koolnova_api/const.py`.
2. **Trailing slash on every path.** `projects/` yes, `projects` no.
3. **At most one request every 30 s.** Koolnova bans your IP automatically above that rate, and
   also on repeated failed logins.
4. **45 s request timeout.** Koolnova support recommends a 45 s per-request timeout (the integration
   default, configurable via `request_timeout` in the options flow). A hung request without a
   timeout would otherwise block a polling cycle forever.

## Common headers

```
accept: application/json, text/plain, */*
accept-language: en
origin: https://app.koolnova.com
referer: https://app.koolnova.com/
cache-control: no-cache
user-agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/148.0.0.0 Safari/537.36
sec-ch-ua: "Chromium";v="148", "Google Chrome";v="148", "Not/A)Brand";v="99"
sec-ch-ua-mobile: ?0
sec-ch-ua-platform: "Windows"
sec-fetch-dest: empty
sec-fetch-mode: cors
sec-fetch-site: same-site
```

Requests with a body add `content-type: application/json` (`PATCH_HEADERS`).
Authenticated requests add `Authorization: Bearer <token>`.

## Authentication

### `POST /auth/v2/login/`

The identifier goes in the **`email`** field. This is the most fragile detail in the whole
integration:

| Payload | Response |
|---|---|
| `{"email": "...", "password": "..."}` | `200` + token |
| `{"username": "...", "password": "..."}` | `400 "Unable to log in with provided credentials"` |

Do not change it without checking against the live API: sending `username` broke login in v1.3.0
and had to be reverted in v1.3.1.

```json
{ "email": "user@example.com", "password": "…" }
```

The response carries the token in `access_token` (the client also accepts `token` and
`accessToken`). It lives for roughly one hour; the client renews it after **50 minutes**
(`TOKEN_LIFETIME` in `client.py`).

On `429` the client retries with exponential backoff (5 attempts, capped at 60 s), honouring the
`Retry-After` header when present. After a failed login it waits `AUTH_FAILURE_COOLDOWN` (300 s)
before retrying.

## Endpoints

### `GET /projects/`

List of projects. The same query parameters as the webapp are sent:

```
page=1  page_size=25  ordering=-start_date  search=  is_oem=false
```

From each item in `data[]` the client uses `name` and, inside `topic`: `id`, `name`, `mode`,
`is_stop`, `is_online`, `eco`, `last_sync`.

### `GET /topics/sensors/`

List of sensors (zones). From each item in `data[]` the client uses `id`, `name`, `status`,
`temperature`, `setpoint_temperature`, `humidity`, `speed`, `updated_at` and the `topic_info` block
(which provides the topic `id` and the connectivity data: RSSI, online, sync).

Fields seen on each zone as of November 2026:

| Field | Meaning |
|---|---|
| `humidity` | Relative humidity in %, e.g. `54.0`. `null` when the zone has no humidity probe |
| `co2` | CO₂ reading in ppm; `null` on zones without a CO₂ probe |
| `room` / `floor` | `{id, name}` grouping (not consumed) |
| `control_unit`, `zone` | Control unit number and zone index, as shown in the webapp (`uc: 31 / zone: 04`) |
| `is_trv`, `is_removed`, `image` | Not consumed |

`topic_info.humidity` is a **different, project-level boolean** (it reads `false` on accounts whose
zones do report humidity), so don't use it to decide whether a zone has a humidity reading.

### `PUT /topics/sensors/{sensor_id}/`

Updates one zone. **It is `PUT`, not `PATCH`** — unlike the topics endpoint.

| Payload | Effect |
|---|---|
| `{"setpoint_temperature": 24.5}` | Target temperature |
| `{"status": "00"}` | Zone mode (see table) |
| `{"speed": "2"}` | Fan speed (see table) |

### `PATCH /topics/{topic_id}/`

Updates the whole project.

| Payload | Effect |
|---|---|
| `{"mode": "1"}` | Global mode (see table) |
| `{"eco": true}` | ECO mode |
| `{"is_stop": true}` | Global stop |
| `{"is_online": true}` | Online state |

## Hub / legacy controller endpoints

Legacy Koolnova controllers (a physical hub instead of per-zone devices) expose a few extra
endpoints. These were contributed from a community fork and are covered by mocked unit tests only —
**not verified against the live API**; if your account has no hub, `/modules/` answers nothing
usable and the integration simply creates no hub entities.

### `GET /modules/`

Lists the modules on the account, one dict per module. The client classifies them by
`ModuleType_Id` (`1` => koolnova zone device, `2` => hub) and uses `Serial` as the id:

```json
[{"Serial": "KN1234", "ModuleType_Id": 2, "…": "…"}]
```

### `GET /hub/{hub_id}/state`

Current state of one hub:

| Field | Meaning |
|---|---|
| `stateEquipment` | Hub is on (`true`/`false`) |
| `behavior` | Behavior mode: `manual`, `auto`, `planning` |

### `PUT /hub/{hub_id}/mode/{target}`

Sets the hub behavior mode. `target` is one of `manual`, `auto`, `planning`. The response mirrors
`/hub/{id}/state`.

### `POST /hub/{hub_id}/Manual/{bool}`

Turns the hub on/off (`True`/`False`). The client then re-reads `/hub/{id}/state` to return the
new state.

### `GET /devices/`

Fallback data source: flat list of devices with a nested `sensor` dict. Used by the coordinator
only when the `topics` endpoints fail, so the integration degrades instead of going `unavailable`.

### `GET /notifications/`

Lists notifications. Currently not consumed by the integration; exposed for tooling.

## Code tables

Defined in `custom_components/koolnova/const.py`. **Project modes and zone modes use different
encodings** — an easy mistake to make.

### Project mode (`mode`)

| Code | HA mode |
|---|---|
| `"1"` | `cool` |
| `"2"` | `off` |
| `"4"` | `heat` |
| `"6"` | `auto` |

### Zone status (`status`)

| Code | HA mode |
|---|---|
| `"00"` | `cool` |
| `"01"` | `heat` |
| `"02"` | `off` |
| `"03"` | `auto` |

### Fan speed (`speed`)

| Code | HA speed |
|---|---|
| `"1"` | `low` |
| `"2"` | `medium` |
| `"3"` | `high` |
| `"4"` | `auto` |

## Error codes

| Code | Usual cause |
|---|---|
| `400` | Malformed payload, value out of range, or `username` instead of `email` on login |
| `404` | **Almost always missing browser-like headers** — not a missing route. Also a path without a trailing slash, or a non-existent ID |
| `429` | Rate limited; the client retries with backoff |
| `5xx` | API down; the client retries with a short backoff |
