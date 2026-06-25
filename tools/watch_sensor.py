"""Xem CHI TIẾT dữ liệu A1 publish lên smart-campus/events/sensor.

Chạy:  python tools/watch_sensor.py
Cần:   pip install paho-mqtt
Dừng:  Ctrl+C
"""
import ssl
import json
from datetime import datetime
from paho.mqtt import client as mqtt

HOST = "f6f78e87db4a4c189dd3d706745a5e93.s1.eu.hivemq.cloud"
PORT = 8883
USER = "DVKN_IOT_2026"
PWD = "ThaiBao12A@"
TOPIC = "smart-campus/events/sensor"

count = 0


def on_connect(c, u, flags, rc, props=None):
    print(f"[MQTT] connected rc={rc}")
    c.subscribe(TOPIC)
    print(f"[MQTT] dang nghe: {TOPIC}  (chi hien event cua A1 = team-iot)\n")


def on_message(c, u, msg):
    global count
    try:
        data = json.loads(msg.payload.decode("utf-8"))
    except Exception as e:
        print("parse error:", e)
        return

    # Chi lay event cua A1, bo qua nhom khac dung chung topic (vd b1-iot)
    if data.get("source_service") != "team-iot":
        return

    count += 1
    now = datetime.now().strftime("%H:%M:%S")
    print(f"================ #{count}  {now}  (status={data.get('status')}) ================")
    print(json.dumps(data, ensure_ascii=False, indent=2))
    print()


cli = mqtt.Client(protocol=mqtt.MQTTv5)
cli.username_pw_set(USER, PWD)
cli.tls_set(tls_version=ssl.PROTOCOL_TLS_CLIENT)
cli.on_connect = on_connect
cli.on_message = on_message
cli.connect(HOST, PORT)
cli.loop_forever()
