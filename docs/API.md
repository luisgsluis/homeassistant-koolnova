# Documentación API Koolnova

Esta integración consume la API REST de Koolnova para controlar sistemas HVAC. La API está implementada con Django REST framework y está disponible en https://api.koolnova.com/.

## Endpoints Utilizados

### GET /projects/
- **Descripción**: Obtiene la lista de proyectos
- **Parámetros de consulta**:
  - `page`: 1
  - `page_size`: 25
  - `ordering`: -start_date
  - `search`: ""
  - `is_oem`: false
- **Respuesta**: Lista de proyectos con información de topic

### GET /topics/sensors/
- **Descripción**: Obtiene la lista de sensores/zonas
- **Respuesta**: Lista de sensores con temperatura, setpoint, status, velocidad

### PATCH /topics/sensors/{sensor_id}/
- **Descripción**: Actualiza un sensor específico
- **Parámetros**:
  - `sensor_id`: ID del sensor
- **Payloads admitidos**:
  - `{"setpoint_temperature": float}` - Temperatura objetivo
  - `{"status": "00|01|02|03"}` - Estado HVAC (COOL/HEAT/OFF/AUTO)
  - `{"speed": "1|2|3|4"}` - Velocidad ventilador (LOW/MEDIUM/HIGH/AUTO)

### PATCH /topics/{topic_id}/
- **Descripción**: Actualiza un proyecto/topic
- **Parámetros**:
  - `topic_id`: ID del topic/proyecto
- **Payloads admitidos**:
  - `{"mode": "1|2|4|6"}` - Modo proyecto (COOL/OFF/AUTO/HEAT)
  - `{"eco": boolean}` - Modo ECO
  - `{"is_online": boolean}` - Estado online
  - `{"is_stop": boolean}` - Estado stop

## Headers Requeridos

Todos los requests deben incluir:

```
User-Agent: Mozilla/5.0 (REQUIRED)
accept: application/json, text/plain, */*
accept-language: fr
origin: https://app.koolnova.com
referer: https://app.koolnova.com/
cache-control: no-cache
content-type: application/json (para PATCH)
```

## Payloads de Ejemplo

### Actualizar temperatura de zona
```json
{
  "setpoint_temperature": 24.5
}
```

### Cambiar modo HVAC de zona
```json
{
  "status": "00"
}
```

### Cambiar velocidad ventilador
```json
{
  "speed": "2"
}
```

### Cambiar modo del proyecto
```json
{
  "mode": "1"
}
```

## Errores Típicos

### 400 Bad Request
- **Causa**: Payload mal formado o parámetros inválidos
- **Solución**: Verificar que los valores estén en el rango permitido

### 404 Not Found
- **Causa**: Endpoint incorrecto o ID no existe
- **Solución**: Verificar IDs y URLs

### Error de Autenticación
- **Causa**: Credenciales inválidas o sesión expirada
- **Solución**: Reconfigurar la integración con credenciales correctas

## Mapeos de Códigos

### Modos Proyecto
- `"1"`: COOL
- `"2"`: OFF
- `"4"`: AUTO
- `"6"`: HEAT

### Estados Zona
- `"00"`: COOL
- `"01"`: HEAT
- `"02"`: OFF
- `"03"`: AUTO

### Velocidades Ventilador
- `"1"`: LOW
- `"2"`: MEDIUM
- `"3"`: HIGH
- `"4"`: AUTO
