# ============================================================
#  AquaNova Control Blueprint
#  Điều khiển cho ăn và quản lý lịch cho ăn
# ============================================================

from flask import Blueprint, request, jsonify, current_app
import paho.mqtt.client as mqtt
import json, uuid, time
from firebase_admin import firestore

control_bp = Blueprint("control_bp", __name__)
_mqtt_pub_client = None


# ------------------------------------------------------------
# MQTT client helper
# ------------------------------------------------------------
def _get_pub():
    global _mqtt_pub_client
    if _mqtt_pub_client:
        return _mqtt_pub_client

    cfg = current_app.config
    client = mqtt.Client(
        mqtt.CallbackAPIVersion.VERSION2,
        client_id="aquanova-control-pub"
    )
    user = cfg.get("MQTT_USER")
    if user:
        client.username_pw_set(user, cfg.get("MQTT_PASS"))

    client.tls_set()
    client.connect(cfg.get("MQTT_HOST"), int(cfg.get("MQTT_PORT", 8883)), keepalive=60)
    client.qos = 1   
    _mqtt_pub_client = client
    return _mqtt_pub_client


# ------------------------------------------------------------
# 🐟 Cho ăn ngay lập tức
# ------------------------------------------------------------
@control_bp.post("/feed-now")
def feed_now():
    data = request.get_json(force=True) or {}
    amount = data.get("amount", 20)

    try:
        topic = "aquanova/control"
        payload = {"feeding": 1}
        print(f"[FEED-NOW] Publishing {payload} → {topic}")

        _get_pub().publish(topic, json.dumps(payload), qos=1)

        # Ghi log Firestore
        db = firestore.client()
        db.collection("feed_logs").add({
            "timestamp": firestore.SERVER_TIMESTAMP,
            "source": "manual"
        })

        return jsonify({"ok": True, "published": {"topic": topic, "payload": payload}})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ------------------------------------------------------------
# 📅 Tạo lịch cho ăn
# ------------------------------------------------------------
@control_bp.post("/schedule")
def add_schedule():
    """
    Thêm lịch cho ăn mới:
      - date: YYYY-MM-DD
      - time: HH:MM
      - repeat: 'none' | 'daily' | 'weekly'
      - amount: số gram thức ăn
    """
    data = request.get_json(force=True) or {}
    required = ("date", "time", "repeat")
    for key in required:
        if not data.get(key):
            return jsonify({"error": f"{key} required"}), 400

    sid = uuid.uuid4().hex[:12]
    item = {
        "id": sid,
        "date": data.get("date", ""),               # ngày (định dạng YYYY-MM-DD)
        "time": data["time"],                       # giờ (HH:MM)
        "repeat": data["repeat"],                   # none / daily / weekly
        "created_at": int(time.time())
    }

    db = firestore.client()
    db.collection("schedules").document(sid).set(item)
    print(f"[SCHEDULE] Added: {item}")

    return jsonify({"ok": True, "id": sid, "item": item})


# ------------------------------------------------------------
# 📋 Danh sách lịch
# ------------------------------------------------------------
@control_bp.get("/schedules")
def list_schedules():
    try:
        db = firestore.client()
        docs = db.collection("schedules").stream()
        items = [doc.to_dict() for doc in docs]
        return jsonify({"items": items})
    except Exception as e:
        print("[ERROR] list_schedules:", e)
        return jsonify({"error": str(e)}), 500


# ------------------------------------------------------------
# 🗑️ Xóa lịch
# ------------------------------------------------------------
@control_bp.delete("/schedules/<sid>")
def delete_schedule(sid):
    try:
        db = firestore.client()
        ref = db.collection("schedules").document(sid)
        if not ref.get().exists:
            return jsonify({"error": "Schedule not found"}), 404
        ref.delete()
        print(f"[SCHEDULE] Deleted {sid}")
        return jsonify({"ok": True})
    except Exception as e:
        print("[ERROR] delete_schedule:", e)
        return jsonify({"error": str(e)}), 500
