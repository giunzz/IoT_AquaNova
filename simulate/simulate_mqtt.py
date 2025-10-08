import json, time, random, threading
from datetime import datetime, timezone
import paho.mqtt.client as mqtt
import os

# ==== Config HiveMQ Cloud ====
HOST = os.getenv("MQTT_HOST", "d2b2655505394c9b8e88c06c8d30d912.s1.eu.hivemq.cloud")
PORT = int(os.getenv("MQTT_PORT", "8883"))  
USER = os.getenv("MQTT_USER", "aquanova_user")
PASS = os.getenv("MQTT_PASS", "12345678Aqua")
BASE_TOPIC = os.getenv("MQTT_BASE", "aquanova/devices")

LOG_FILE = "mqtt_log.txt"
log_lock = threading.Lock()  # tránh conflict khi nhiều thread ghi cùng lúc

def write_log(msg: str):
    """Ghi log ra file và in ra màn hình."""
    line = f"{datetime.now().isoformat()} {msg}"
    with log_lock:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(line + "\n")
    print(line)

def gen(device_id):
    return {
        "device_id": device_id,
        "ts": datetime.now(timezone.utc).isoformat(),
        "temperature": round(random.uniform(24, 31), 2),
        "turbidity": round(random.uniform(10, 80), 2),
        "feed": round(random.uniform(0, 100), 1)
    }

def run_device(device_id, every=5, total=40):
    client_id = f"sim-{device_id}"
    c = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id=client_id)
    if USER:
        c.username_pw_set(USER, PASS)

    c.tls_set()
    c.tls_insecure_set(True)

    def on_connect(client, userdata, flags, reason_code, properties=None):
        write_log(f"[{device_id}] Connected with result code {reason_code}")

    def on_publish(client, userdata, mid, reason_code=None, properties=None):
        write_log(f"[{device_id}] Published mid={mid}, reason={reason_code}")

    def on_disconnect(client, userdata, reason_code, properties=None):
        write_log(f"[{device_id}] Disconnected, reason={reason_code}")

    def on_log(client, userdata, level, buf):
        write_log(f"[{device_id}] log: {buf}")

    c.on_connect = on_connect
    c.on_publish = on_publish
    c.on_disconnect = on_disconnect
    c.on_log = on_log

    c.connect(HOST, PORT, 60)
    topic = f"{BASE_TOPIC}/{device_id}/telemetry"

    c.loop_start()
    for _ in range(total):
        payload = gen(device_id)
        c.publish(topic, json.dumps(payload), qos=1)
        write_log(f"[{device_id}] -> publishing {payload} to {topic}")
        time.sleep(every)
    c.loop_stop()
    c.disconnect()

if __name__ == "__main__":
    for i, dev in enumerate(["sensor-1", "sensor-2", "sensor-3"]):
        threading.Thread(target=run_device, args=(dev, 5, 10), daemon=True).start()
        time.sleep(0.2 + i * 0.1)

    while True:
        time.sleep(1)
