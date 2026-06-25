# MQTT Data Contract - IoT Ingestion Service (Demo Day)

## Input Topic: `smart-campus/raw/iot/environment`

**Mô tả:** Nhận telemetry thô từ Gateway hoặc Thiết bị đầu cuối (ESP32). Payload bắt buộc là JSON, phải có timestamp hợp lệ (ISO 8601 kèm timezone).

**Ví dụ Payload Hợp Lệ:**
```json
{
  "event_id": "raw-12345",
  "event_type": "iot.environment.sampled",
  "timestamp": "2026-06-15T15:00:00+07:00",
  "device_id": "ESP32-LAB-A01",
  "temperature_c": 35.5,
  "humidity_percent": 60,
  "motion_detected": false,
  "light_lux": 420,
  "co2_ppm": 800,
  "smoke_ppm": 0.0,
  "battery_percent": 90
}
```

## Output Topic: `smart-campus/events/sensor`

**Mô tả:** Sau khi đi qua Rule Engine của nhóm A1, dữ liệu được "đóng dấu" (processed) và phân loại trạng thái (normal, warning, danger, sensor_error, invalid_device). Nhóm Analytics (C) và Dashboard (D) sẽ subscribe topic này.

**Ví dụ Payload Hợp Lệ:**
```json
{
  "event_id": "sensor-event-a1b2c3d4",
  "event_type": "sensor.reading.processed",
  "source_service": "team-iot",
  "timestamp": "2026-06-15T15:00:02+07:00",
  "raw_event_id": "raw-12345",
  "device_id": "ESP32-LAB-A01",
  "location": "Unknown",
  "temperature_c": 35.5,
  "humidity_percent": 60.0,
  "motion_detected": false,
  "light_lux": 420,
  "co2_ppm": 800.0,
  "smoke_ppm": 0.0,
  "battery_percent": 90.0,
  "status": "warning",
  "alert_level": "medium",
  "reason": "high_temperature"
}
```

## Validation Rules

- Missing any required field (`event_id`, `event_type`, `timestamp`, `device_id`,
  `temperature_c`, `humidity_percent`, `motion_detected`) causes the message to
  be logged and dropped.
- `event_type` must be `iot.environment.sampled`.
- `timestamp` must be ISO 8601 and include a timezone.
- Invalid or null sensor values produce `status=sensor_error`.
- Unknown devices produce `status=invalid_device`.
- `scenario_hint_for_teacher` is never forwarded.

Messages use QoS 1 on both topics.
