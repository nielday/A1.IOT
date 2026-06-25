import json
import logging
import os
import ssl
import csv
from collections import deque
from datetime import datetime
from uuid import uuid4

from paho.mqtt import client as mqtt
from paho.mqtt.enums import CallbackAPIVersion

logger = logging.getLogger(__name__)

# Constants (No fallback credentials)
MQTT_HOST = os.getenv("MQTT_HOST", "f6f78e87db4a4c189dd3d706745a5e93.s1.eu.hivemq.cloud")
MQTT_PORT = int(os.getenv("MQTT_PORT", 8883))
MQTT_USERNAME = os.getenv("MQTT_USERNAME", "")
MQTT_PASSWORD = os.getenv("MQTT_PASSWORD", "")
MQTT_INPUT_TOPIC = os.getenv("MQTT_INPUT_TOPIC", "smart-campus/raw/iot/environment")
MQTT_OUTPUT_TOPIC = os.getenv("MQTT_OUTPUT_TOPIC", "smart-campus/events/sensor")

# Global State
mqtt_state = {
    "connected": False,
    "client": None
}

# Registry
VALID_DEVICES = set()

# Buffer event đã xử lý gần nhất (cho dashboard hiển thị) — newest first
recent_events = deque(maxlen=50)

def get_mqtt_status() -> dict:
    return {"connected": bool(mqtt_state["connected"])}

def get_recent_events() -> list:
    return list(recent_events)

def load_device_registry():
    registry_path = os.path.join(os.path.dirname(__file__), 'data', 'IoT_device_registry.csv')
    try:
        VALID_DEVICES.clear()
        with open(registry_path, mode='r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                VALID_DEVICES.add(row['device_id'])
        logger.info(f"Loaded {len(VALID_DEVICES)} devices from registry.")
    except Exception as e:
        logger.error(f"Failed to load device registry: {e}")

def parse_bool(value):
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        if value.strip().lower() in ["true", "1"]:
            return True
        if value.strip().lower() in ["false", "0"]:
            return False
    if isinstance(value, int) and value in [0, 1]:
        return bool(value)
    raise ValueError(f"Cannot parse boolean from {value}")

def parse_float(value):
    if isinstance(value, bool):
        raise TypeError("Boolean passed to float parser")
    return float(value)

def parse_timestamp(value):
    if not isinstance(value, str):
        raise ValueError("Timestamp must be a string")
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ValueError("Timestamp must include a timezone")
    return parsed

def decode_payload(payload: bytes) -> dict | None:
    try:
        decoded = json.loads(payload.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        logger.error("Failed to parse MQTT payload as JSON")
        return None

    if not isinstance(decoded, dict):
        logger.error("MQTT payload must be a JSON object")
        return None
    return decoded

def on_connect(client, userdata, flags, reason_code, properties=None):
    if reason_code.is_failure:
        logger.error(f"Failed to connect to HiveMQ: {reason_code}")
        mqtt_state["connected"] = False
    else:
        logger.info("Connected to HiveMQ successfully.")
        mqtt_state["connected"] = True
        client.subscribe(MQTT_INPUT_TOPIC, qos=1)
        logger.info(f"Subscribed to topic: {MQTT_INPUT_TOPIC}")

def on_disconnect(client, userdata, flags, reason_code, properties=None):
    logger.warning(f"Disconnected from HiveMQ. Reason: {reason_code}")
    mqtt_state["connected"] = False

def process_payload(raw_data):
    # 1. Schema Validation (Drop if invalid)
    required_fields = [
        'event_id',
        'event_type',
        'timestamp',
        'device_id',
        'temperature_c',
        'humidity_percent',
        'motion_detected',
    ]
    for field in required_fields:
        if field not in raw_data:
            logger.warning(f"Schema Validation failed: missing {field}")
            return None
            
    if raw_data['event_type'] != "iot.environment.sampled":
        logger.warning(f"Schema Validation failed: unknown event_type '{raw_data['event_type']}'")
        return None
        
    try:
        parse_timestamp(raw_data['timestamp'])
    except (TypeError, ValueError):
        logger.warning("Schema Validation failed: invalid ISO 8601 timestamp")
        return None
            
    # Remove teacher hint
    raw_data.pop('scenario_hint_for_teacher', None)
    
    device_id = raw_data['device_id']
    
    status = "normal"
    alert_level = "none"
    reason = "environment_normal"
    
    # 2. Check Device Registry
    if device_id not in VALID_DEVICES:
        status = "invalid_device"
        alert_level = "high"
        reason = "device_not_registered"
        
    # Variables for typed data
    temp = hum = co2 = smoke = battery = motion = None

    # 3. Parse and Validate Sensor Data
    # Parse each field independently so valid readings are preserved
    # even when a single sensor returns a bad/null value (theo mẫu payload 9.4).
    sensor_error = False

    def parse_sensor(parser, value):
        nonlocal sensor_error
        try:
            return parser(value)
        except (ValueError, TypeError, KeyError) as e:
            logger.warning(f"Sensor Error parsing data for device {device_id}: {e}")
            sensor_error = True
            return None

    temp = parse_sensor(parse_float, raw_data['temperature_c'])
    hum = parse_sensor(parse_float, raw_data['humidity_percent'])
    co2 = parse_sensor(parse_float, raw_data.get('co2_ppm', 0))
    smoke = parse_sensor(parse_float, raw_data.get('smoke_ppm', 0.0))
    battery = parse_sensor(parse_float, raw_data.get('battery_percent', 100))
    motion = parse_sensor(parse_bool, raw_data['motion_detected'])

    if sensor_error and status == "normal":
        status = "sensor_error"
        alert_level = "medium"
        reason = "missing_sensor_value"
        
    # 4. Classify Rules (only if not invalid_device and not sensor_error)
    if status == "normal":
        if temp >= 40 or co2 >= 1800 or smoke >= 1.0:
            status = "danger"
            alert_level = "high"
            if temp >= 40: reason = "temperature_too_high"
            elif co2 >= 1800: reason = "co2_dangerous"
            else: reason = "smoke_detected"
            
        elif temp >= 35 or hum >= 85 or co2 >= 1200 or smoke >= 0.5 or battery < 20:
            status = "warning"
            alert_level = "medium"
            if temp >= 35: reason = "high_temperature"
            elif hum >= 85: reason = "high_humidity"
            elif co2 >= 1200: reason = "high_co2"
            elif smoke >= 0.5: reason = "smoke_warning"
            else: reason = "low_battery"

    # 5. Build Processed Event
    current_time = datetime.now().astimezone().isoformat()
    
    processed_event = {
        "event_id": f"sensor-event-{uuid4().hex[:8]}",
        "event_type": "sensor.reading.processed",
        "source_service": "team-iot",
        "timestamp": current_time,
        "raw_event_id": raw_data['event_id'],
        "device_id": device_id,
        "location": raw_data.get('location', 'Unknown'),
        "temperature_c": temp,
        "humidity_percent": hum,
        "motion_detected": motion,
        "light_lux": raw_data.get('light_lux', 0),
        "co2_ppm": co2,
        "smoke_ppm": smoke,
        "battery_percent": battery,
        "status": status,
        "alert_level": alert_level,
        "reason": reason
    }
    
    return processed_event

def on_message(client, userdata, message):
    raw_data = decode_payload(message.payload)
    if raw_data is None:
        return
        
    logger.info(f"Received raw data for device: {raw_data.get('device_id')}")
    
    try:
        processed_event = process_payload(raw_data)
        if processed_event:
            client.publish(MQTT_OUTPUT_TOPIC, json.dumps(processed_event), qos=1)
            logger.info(f"Processed status: {processed_event['status']}, published to {MQTT_OUTPUT_TOPIC}")
            # Lưu vào buffer cho dashboard (newest first)
            recent_events.appendleft({**processed_event, "received_at": datetime.now().astimezone().isoformat()})
    except Exception as e:
        logger.error(f"Error processing MQTT message: {e}", exc_info=True)

def on_publish(client, userdata, mid, reason_code, properties=None):
    logger.debug(f"MQTT publish acknowledged: mid={mid}, reason={reason_code}")

def get_mqtt_client():
    client = mqtt.Client(callback_api_version=CallbackAPIVersion.VERSION2, protocol=mqtt.MQTTv5)
    if MQTT_USERNAME and MQTT_PASSWORD:
        client.username_pw_set(MQTT_USERNAME, MQTT_PASSWORD)
    client.tls_set(tls_version=ssl.PROTOCOL_TLS_CLIENT)
    
    # Configure auto-reconnect backoff
    client.reconnect_delay_set(min_delay=1, max_delay=120)
    
    client.on_connect = on_connect
    client.on_disconnect = on_disconnect
    client.on_message = on_message
    client.on_publish = on_publish
    
    return client

def start_mqtt_worker():
    load_device_registry()
    client = get_mqtt_client()
    mqtt_state["client"] = client
    try:
        # loop_start does non-blocking connect in background
        client.connect_async(MQTT_HOST, MQTT_PORT)
        client.loop_start() 
        logger.info("MQTT loop_start initialized.")
    except Exception as e:
        logger.error(f"Could not initialize MQTT loop: {e}")

def stop_mqtt_worker():
    client = mqtt_state.get("client")
    if client:
        logger.info("Stopping MQTT worker...")
        client.disconnect()
        client.loop_stop()
        mqtt_state["client"] = None
        mqtt_state["connected"] = False
        logger.info("MQTT worker stopped.")
