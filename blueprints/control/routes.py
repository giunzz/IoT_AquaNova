# blueprints/control/routes.py
from flask import Blueprint, request, jsonify, current_app
import paho.mqtt.client as mqtt
import json, uuid, time
from firebase_admin import firestore

control_bp = Blueprint("control_bp", __name__)
_mqtt_pub_client = None


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
    client.connect(
        cfg.get("MQTT_HOST", "localhost"),
        int(cfg.get("MQTT_PORT", 8883)),
        keepalive=60
    )

    _mqtt_pub_client = client
    return _mqtt_pub_client



@control_bp.post("/feed-now")
def feed_now():
    data = request.get_json(force=True) or {}
    amount = data.get("amount", 20)

    try:
        topic = "aquanova/control"
        payload = {"cmd": "feed", "amount": amount}
        print(payload)

        # Publish ngay lập tức
        _get_pub().publish(topic, json.dumps(payload), qos=1)

        # Ghi log vào Firestore
        db = firestore.client()
        db.collection("feed_logs").add({
            "amount": amount,
            "timestamp": firestore.SERVER_TIMESTAMP
        })

        return jsonify({"ok": True, "published": {"topic": topic, "payload": payload}})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@control_bp.post("/schedule")
def add_schedule():
    data = request.get_json(force=True) or {}
    for key in ("time", "repeat", "amount"):
        if not data.get(key):
            return jsonify({"error": f"{key} required"}), 400

    sid = uuid.uuid4().hex[:12]
    item = {
        "id": sid,
        "time": data["time"],           # dạng "HH:MM"
        "repeat": bool(data["repeat"]), # True/False
        "amount": int(data["amount"]),
        "created_at": int(time.time()),
    }

    db = firestore.client()
    db.collection("schedules").document(sid).set(item)

    print(f"[SCHEDULE] Added: {item}")

    return jsonify({"ok": True, "id": sid, "item": item})


# ====================================================
# 📋 Danh sách lịch
# ====================================================
@control_bp.get("/schedules")
def list_schedules():
    db = firestore.client()
    docs = db.collection("schedules").stream()
    items = [doc.to_dict() for doc in docs]
    return jsonify({"items": items})


# ====================================================
# 🗑️ Xóa lịch
# ====================================================
@control_bp.delete("/schedules/<sid>")
def delete_schedule(sid):
    db = firestore.client()
    doc_ref = db.collection("schedules").document(sid)
    if doc_ref.get().exists:
        doc_ref.delete()
        print(f"[SCHEDULE] Deleted {sid}")
        return jsonify({"ok": True})
    return jsonify({"error": "not found"}), 404



# Firestore structure:
# feed_logs/
#   ├── autoID1: {amount, timestamp}
# schedules/
#   ├── 7e31c2d4ab12: {id, time, repeat, amount, created_at}
# =====================================
