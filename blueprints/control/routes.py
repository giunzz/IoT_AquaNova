# blueprints/control/routes.py
from flask import Blueprint, request, jsonify, current_app
import paho.mqtt.client as mqtt

control_bp = Blueprint("control_bp", __name__)
_mqtt_pub_client = None

def _get_pub():
    global _mqtt_pub_client
    if _mqtt_pub_client: return _mqtt_pub_client
    c = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
    cfg = current_app.config
    if cfg.get("MQTT_USER"):
        c.username_pw_set(cfg["MQTT_USER"], cfg["MQTT_PASS"])
    c.connect(cfg["MQTT_HOST"], int(cfg["MQTT_PORT"]), 60)
    _mqtt_pub_client = c
    return c

@control_bp.post("/feed-now")
def feed_now():
    data = request.get_json(force=True)
    device = data.get("device_id")
    amount = data.get("amount", 20)
    if not device: return jsonify({"error":"device_id required"}), 400
    topic = f"aquanova/devices/{device}/control"
    payload = {"cmd":"feed","amount":amount}
    _get_pub().publish(topic, json.dumps(payload), qos=1)
    return jsonify({"ok":True})
