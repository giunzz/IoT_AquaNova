import json, time, random, threading
from datetime import datetime, timezone
import paho.mqtt.client as mqtt
import os

HOST = os.getenv("MQTT_HOST","localhost")
PORT = int(os.getenv("MQTT_PORT","1883"))
USER = os.getenv("MQTT_USER","")
PASS = os.getenv("MQTT_PASS","")
BASE_TOPIC = os.getenv("MQTT_BASE","aquanova/devices")

def gen(device_id):
    return {
        "device_id": device_id,
        "ts": datetime.now(timezone.utc).isoformat(),
        "temperature": round(random.uniform(24,31),2),
        "turbidity": round(random.uniform(10,80),2),
        "feed": round(random.uniform(0,100),1)
    }

def run_device(device_id, every=5, total=40):
    c = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
    if USER: c.username_pw_set(USER, PASS)
    c.connect(HOST, PORT, 60)
    topic = f"{BASE_TOPIC}/{device_id}/telemetry"
    for _ in range(total):
        payload = gen(device_id)
        c.publish(topic, json.dumps(payload), qos=1)
        print(f"[pub] {device_id} -> {payload}")
        time.sleep(every)
    c.disconnect()

if __name__ == "__main__":
    for i, dev in enumerate(["sensor-1","sensor-2","sensor-3"]):
        threading.Thread(target=run_device, args=(dev, 5, 40), daemon=True).start()
        time.sleep(0.2+i*0.1)
    while True: time.sleep(1)
