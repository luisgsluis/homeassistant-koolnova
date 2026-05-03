# Koolnova API Documentation

This integration consumes the Koolnova REST API to control HVAC systems. The API is implemented with Django REST Framework and is available at `https://api.koolnova.com/`.

## Endpoints Used

### GET `/projects/`
- **Description**: Retrieves the list of projects.
- **Query parameters**:
  - `page`: 1
  - `page_size`: 25
  - `ordering`: `-start_date`
  - `search`: `""`
  - `is_oem`: false
- **Response**: List of projects with topic information.

### GET `/topics/sensors/`
- **Description**: Retrieves the list of sensors/zones.
- **Response**: List of sensors with temperature, setpoint, status, fan speed, etc.

### PATCH `/topics/sensors/{sensor_id}/`
- **Description**: Updates a specific sensor.
- **Path parameter**:
  - `sensor_id`: ID of the sensor.
- **Supported payloads**:
  - `{"setpoint_temperature": float}` – Target temperature.
  - `{"status": "00|01|02|03"}` – HVAC status (COOL/HEAT/OFF/AUTO).
  - `{"speed": "1|2|3|4"}` – Fan speed (LOW/MEDIUM/HIGH/AUTO).

### PATCH `/topics/{topic_id}/`
- **Description**: Updates a project/topic.
- **Path parameter**:
  - `topic_id`: ID of the topic/project.
- **Supported payloads**:
  - `{"mode": "1|2|4|6"}` – Project mode (COOL/OFF/AUTO/HEAT).
  - `{"eco": boolean}` – ECO mode.
  - `{"is_online": boolean}` – Online status.
  - `{"is_stop": boolean}` – Stop status.

## Required Headers

All requests must include:

```
User-Agent: Mozilla/5.0 (REQUIRED)
accept: application/json, text/plain, */*
accept-language: fr
origin: https://app.koolnova.com
referer: https://app.koolnova.com/
cache-control: no-cache
content-type: application/json (for PATCH only)
```

## Example Payloads

### Update zone temperature
```json
{
  "setpoint_temperature": 24.5
}
```

### Change zone HVAC mode
```json
{
  "status": "00"
}
```

### Change fan speed
```json
{
  "speed": "2"
}
```

### Change project mode
```json
{
  "mode": "1"
}
```

## Typical Errors

### 400 Bad Request
- **Cause**: Malformed payload or invalid parameters.
- **Solution**: Verify values are within allowed ranges.

### 404 Not Found
- **Cause**: Incorrect endpoint or ID does not exist.
- **Solution**: Check IDs and URLs.

### Authentication Error
- **Cause**: Invalid or expired credentials.
- **Solution**: Reconfigure integration with correct credentials.

## Code Mappings

### Project Modes
| Code | Meaning |
|------|---------|
| `"1"` | COOL |
| `"2"` | OFF |
| `"4"` | AUTO |
| `"6"` | HEAT |

### Zone Status Codes
| Code | Meaning |
|------|---------|
| `"00"` | COOL |
| `"01"` | HEAT |
| `"02"` | OFF |
| `"03"` | AUTO |

### Fan Speed Codes
| Code | Meaning |
|------|---------|
| `"1"` | LOW |
| `"2"` | MEDIUM |
| `"3"` | HIGH |
| `"4"` | AUTO |