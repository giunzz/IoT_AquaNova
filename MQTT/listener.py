# mqtt/listener.py
import json, threading, time
import paho.mqtt.client as mqtt
from datetime import datetime, timezone
from firebase_admin_init import init_firebase

LOG_FILE = "mqtt_sub_log.txt"
log_lock = threading.Lock()

def write_log(msg: str):
    line = f"{datetime.now().isoformat()} {msg}"
    with log_lock:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(line + "\n")
    print(line)


def start_mqtt_background(app):
    cfg = app.config
    db = init_firebase()  
    def on_connect(client, userdata, flags, reason_code, properties=None):
        write_log(f"[MQTT] ✅ CONNECTED with code={reason_code}")
        try:
            result, mid = client.subscribe(cfg["MQTT_TOPIC"], qos=1)
            write_log(f"[MQTT] SUBSCRIBE sent topic={cfg['MQTT_TOPIC']} mid={mid} result={result}")
        except Exception as e:
            write_log(f"[MQTT] ❌ SUBSCRIBE ERROR: {e}")

    def on_disconnect(client, userdata, rc, properties=None):
        write_log(f"[MQTT] ⚠️ DISCONNECTED (rc={rc}) — will attempt reconnect")
        while True:
            try:
                client.reconnect()
                write_log("[MQTT] 🔁 RECONNECTED successfully!")
                break
            except Exception as e:
                write_log(f"[MQTT] ❌ Reconnect failed: {e}")
                time.sleep(5)  # chờ 5 giây rồi thử lại

    def on_subscribe(client, userdata, mid, granted_qos, properties=None):
        write_log(f"[MQTT] SUBACK mid={mid}, granted_qos={granted_qos}")

    def on_message(client, userdata, msg):
        try:
            payload = msg.payload.decode("utf-8", errors="ignore")
            data = json.loads(payload)
            data.setdefault("ts", datetime.now(timezone.utc).isoformat())
            data["deviceId"] = data.get("deviceId") or data.get("device_id")
            db.collection("readings").add(data)
            write_log(f"[MQTT] 📩 MESSAGE topic={msg.topic} payload={data}")
        except Exception as e:
            write_log(f"[MQTT] ❌ ERROR: {e} | payload={msg.payload[:200]}")

    client = mqtt.Client(
        mqtt.CallbackAPIVersion.VERSION2,
        client_id="aquanova-server",
        clean_session=True
    )

    user, pwd = cfg.get("MQTT_USER"), cfg.get("MQTT_PASS")
    if user:
        client.username_pw_set(user, pwd)

    # TLS cho HiveMQ Cloud
    client.tls_set()
    client.tls_insecure_set(True) 
    client.on_connect = on_connect
    client.on_disconnect = on_disconnect
    client.on_message = on_message
    client.on_subscribe = on_subscribe

    def mqtt_loop():
        while True:
            try:
                write_log(f"[MQTT] 🔌 Connecting to {cfg['MQTT_HOST']}:{cfg['MQTT_PORT']}")
                client.connect(cfg["MQTT_HOST"], int(cfg["MQTT_PORT"]), keepalive=60)
                client.loop_forever(retry_first_connection=True)
            except Exception as e:
                write_log(f"[MQTT] ❌ Connection error: {e}")
                time.sleep(5)

    t = threading.Thread(target=mqtt_loop, daemon=True)
    t.start()
    write_log(f"[MQTT] LISTENING {cfg['MQTT_HOST']}:{cfg['MQTT_PORT']} topic={cfg['MQTT_TOPIC']}")
    return client
