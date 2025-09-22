# blueprints/control/routes.py
from flask import Blueprint, request, jsonify, current_app
import paho.mqtt.client as mqtt
import json, uuid, time

control_bp = Blueprint("control_bp", __name__)

# ===== MQTT publisher (singleton) =====
_mqtt_pub_client = None

def _get_pub():
    """Lấy MQTT client dùng chung, kết nối theo config của app."""
    global _mqtt_pub_client
    if _mqtt_pub_client:
        return _mqtt_pub_client

    cfg = current_app.config
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id="aquanova-control-pub")
    user = cfg.get("MQTT_USER")
    if user:
        client.username_pw_set(user, cfg.get("MQTT_PASS"))
    client.connect(cfg.get("MQTT_HOST", "localhost"), int(cfg.get("MQTT_PORT", 1883)), keepalive=60)

    _mqtt_pub_client = client
    return _mqtt_pub_client

# ===== Lệnh cho ăn ngay =====
@control_bp.post("/feed-now")
def feed_now():
    data = request.get_json(force=True) or {}
    device = data.get("device_id")
    amount = data.get("amount", 20)

    if not device:
        return jsonify({"error": "device_id required"}), 400
    try:
        topic = f"aquanova/devices/{device}/control"
        payload = {"cmd": "feed", "amount": amount}
        _get_pub().publish(topic, json.dumps(payload), qos=1)
        return jsonify({"ok": True, "published": {"topic": topic, "payload": payload}})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ===== Lịch cho ăn (demo lưu RAM) =====
# Bạn có thể thay bằng Firestore sau này.
_SCHEDULES = {}  # id -> schedule dict

@control_bp.post("/schedule")
def add_schedule():
    """
    Body:
      { "device_id":"sensor-1", "time":"08:30", "repeat":"daily|weekly|once", "amount":20 }
    """
    data = request.get_json(force=True) or {}
    for key in ("device_id", "time", "repeat", "amount"):
        if not data.get(key):
            return jsonify({"error": f"{key} required"}), 400

    sid = uuid.uuid4().hex[:12]
    item = {
        "id": sid,
        "device_id": data["device_id"],
        "time": data["time"],           # "HH:mm"
        "repeat": data["repeat"],       # once/daily/weekly
        "amount": data["amount"],
        "created_at": int(time.time()),
    }
    _SCHEDULES[sid] = item
    return jsonify({"ok": True, "id": sid, "item": item})

@control_bp.get("/schedules")
def list_schedules():
    """Trả về danh sách lịch hiện có (để FE render bảng)."""
    return jsonify({"items": list(_SCHEDULES.values())})

@control_bp.delete("/schedules/<sid>")
def delete_schedule(sid):
    if sid in _SCHEDULES:
        del _SCHEDULES[sid]
        return jsonify({"ok": True})
    return jsonify({"error": "not found"}), 404
