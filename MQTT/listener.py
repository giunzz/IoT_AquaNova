# mqtt/listener.py
import json, threading
import paho.mqtt.client as mqtt
from datetime import datetime, timezone
from firebase_admin_init import init_firebase

def start_mqtt_background(app):
    """
    Gọi hàm này trong create_app() sau khi init config/firebase.
    Chạy client.loop_forever() ở thread nền để không chặn Flask.
    """
    cfg = app.config
    db = init_firebase()  # trả về firestore client đã init

    def on_connect(client, userdata, flags, reason_code, properties=None):
        print("[MQTT] connected:", reason_code)
        client.subscribe(cfg["MQTT_TOPIC"], qos=1)

    def on_message(client, userdata, msg):
        try:
            data = json.loads(msg.payload.decode("utf-8"))
            # đảm bảo có timestamp & deviceId
            data.setdefault("ts", datetime.now(timezone.utc).isoformat())
            data["deviceId"] = data.get("deviceId") or data.get("device_id")
            db.collection("readings").add(data)
        except Exception as e:
            print("[MQTT] err:", e, "| payload:", msg.payload[:200])

    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id="aquanova-server", clean_session=True)
    user, pwd = cfg.get("MQTT_USER"), cfg.get("MQTT_PASS")
    if user:
        client.username_pw_set(user, pwd)
    client.on_connect = on_connect
    client.on_message = on_message
    client.connect(cfg["MQTT_HOST"], int(cfg["MQTT_PORT"]), keepalive=60)

    t = threading.Thread(target=client.loop_forever, daemon=True)
    t.start()
    print(f"[MQTT] listening {cfg['MQTT_HOST']}:{cfg['MQTT_PORT']} topic={cfg['MQTT_TOPIC']}")
    return client
