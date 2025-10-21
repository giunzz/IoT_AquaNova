# mqtt/publisher.py
import json
import paho.mqtt.client as mqtt
from datetime import datetime

class MQTTPublisher:

    def __init__(self, app):
        self.app = app
        self.client = mqtt.Client(
            mqtt.CallbackAPIVersion.VERSION2,
            client_id=f"aquanova-publisher-{datetime.now().timestamp()}"
        )

        cfg = app.config
        user, pwd = cfg.get("MQTT_USER"), cfg.get("MQTT_PASS")
        if user:
            self.client.username_pw_set(user, pwd)

        self.client.tls_set()
        self.client.tls_insecure_set(True)

        # Kết nối
        self.client.connect(cfg["MQTT_HOST"], int(cfg["MQTT_PORT"]), keepalive=60)
        self.client.loop_start()  # Duy trì kết nối nền

        print(f"[MQTT] Publisher connected to {cfg['MQTT_HOST']}")

    def publish(self, topic: str, payload: dict, qos: int = 1):
        """Gửi lệnh đến MQTT broker."""
        try:
            msg = json.dumps(payload)
            result = self.client.publish(topic, msg, qos=qos)
            result.wait_for_publish()
            print(f"[MQTT] 📤 Published to {topic}: {msg}")
            return True
        except Exception as e:
            print(f"[MQTT] Publish failed: {e}")
            return False
