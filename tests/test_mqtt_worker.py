import pytest
from datetime import datetime
from fastapi import Response

from src.iot_app.main import health
from src.iot_app.mqtt_worker import (
    VALID_DEVICES,
    decode_payload,
    mqtt_state,
    parse_bool,
    parse_float,
    process_payload,
)

# Setup registry for test
VALID_DEVICES.add("ESP32-LAB-A01")

def get_base_payload():
    return {
        "event_id": "test-123",
        "event_type": "iot.environment.sampled",
        "timestamp": datetime.now().astimezone().isoformat(),
        "device_id": "ESP32-LAB-A01",
        "temperature_c": 25.0,
        "humidity_percent": 60.0,
        "motion_detected": False,
        "co2_ppm": 400.0,
        "smoke_ppm": 0.0,
        "battery_percent": 100
    }

def test_normal_scenario():
    payload = get_base_payload()
    result = process_payload(payload)
    assert result is not None
    assert result["status"] == "normal"
    assert result["alert_level"] == "none"

def test_warning_boundary():
    payload = get_base_payload()
    payload["temperature_c"] = 35.0
    result = process_payload(payload)
    assert result["status"] == "warning"
    assert result["alert_level"] == "medium"
    assert result["reason"] == "high_temperature"

def test_danger_boundary():
    payload = get_base_payload()
    payload["temperature_c"] = 40.0
    result = process_payload(payload)
    assert result["status"] == "danger"
    assert result["alert_level"] == "high"

def test_invalid_device():
    payload = get_base_payload()
    payload["device_id"] = "UNKNOWN-01"
    result = process_payload(payload)
    assert result["status"] == "invalid_device"
    assert result["alert_level"] == "high"
    
def test_missing_required_field():
    payload = get_base_payload()
    del payload["temperature_c"]
    result = process_payload(payload)
    assert result is None  # Dropped by schema validation

def test_null_sensor_value():
    payload = get_base_payload()
    payload["temperature_c"] = None
    result = process_payload(payload)
    assert result["status"] == "sensor_error"
    assert result["alert_level"] == "medium"

def test_wrong_event_type():
    payload = get_base_payload()
    payload["event_type"] = "sensor.reading"
    result = process_payload(payload)
    assert result is None

def test_timestamp_no_timezone():
    payload = get_base_payload()
    payload["timestamp"] = "2026-06-15T15:00:00"  # No TZ
    result = process_payload(payload)
    assert result is None

def test_boolean_string_parsing():
    payload = get_base_payload()
    payload["motion_detected"] = "false"
    result = process_payload(payload)
    assert result["motion_detected"] is False

def test_invalid_boolean_is_sensor_error():
    payload = get_base_payload()
    payload["motion_detected"] = "not-a-boolean"
    result = process_payload(payload)
    assert result["status"] == "sensor_error"
    assert result["motion_detected"] is None

def test_invalid_numeric_parsing():
    payload = get_base_payload()
    payload["temperature_c"] = "invalid_string"
    result = process_payload(payload)
    assert result["status"] == "sensor_error"
    assert result["temperature_c"] is None

def test_sensor_error_keeps_readable_fields_and_reason():
    # Theo payload mẫu 9.4: chỉ field lỗi bị null, field đọc được vẫn giữ;
    # reason đúng contract là "missing_sensor_value".
    payload = get_base_payload()
    payload["temperature_c"] = None
    result = process_payload(payload)
    assert result["status"] == "sensor_error"
    assert result["reason"] == "missing_sensor_value"
    assert result["temperature_c"] is None
    assert result["humidity_percent"] == 60.0  # field hợp lệ được giữ lại
    
def test_co2_string_parsing():
    payload = get_base_payload()
    payload["co2_ppm"] = "1800"
    result = process_payload(payload)
    assert result["status"] == "danger"
    assert result["co2_ppm"] == 1800.0

def test_boolean_to_float_blocked():
    with pytest.raises(TypeError):
        parse_float(True)

def test_malformed_json_is_rejected():
    assert decode_payload(b'{"event_id":') is None
    assert decode_payload(b'[]') is None

def test_teacher_hint_is_not_forwarded():
    payload = get_base_payload()
    payload["scenario_hint_for_teacher"] = "danger"
    result = process_payload(payload)
    assert "scenario_hint_for_teacher" not in result

def test_invalid_device_has_priority_over_bad_sensor():
    payload = get_base_payload()
    payload["device_id"] = "UNKNOWN-01"
    payload["temperature_c"] = "invalid"
    result = process_payload(payload)
    assert result["status"] == "invalid_device"
    assert result["reason"] == "device_not_registered"

def test_health_reports_mqtt_state():
    mqtt_state["connected"] = False
    response = Response()
    body = health(response)
    assert response.status_code == 503
    assert body.status == "error"
    assert body.mqtt == "disconnected"

    mqtt_state["connected"] = True
    response = Response()
    body = health(response)
    assert response.status_code == 200
    assert body.status == "ok"
    assert body.mqtt == "connected"
