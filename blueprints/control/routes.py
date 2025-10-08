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
    client.tls_set()  # HiveMQ Cloud yêu cầu TLS
    client.connect(cfg.get("MQTT_HOST", "localhost"),
                   int(cfg.get("MQTT_PORT", 8883)),
                   keepalive=60)
    _mqtt_pub_client = client
    return _mqtt_pub_client


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

        # publish MQTT
        _get_pub().publish(topic, json.dumps(payload), qos=1)

        db = firestore.client()
        db.collection("feed_logs").add({
            "device_id": device,
            "amount": amount,
            "timestamp": firestore.SERVER_TIMESTAMP
        })

        return jsonify({"ok": True, "published": {"topic": topic, "payload": payload}})
    except Exception as e:
        return jsonify({"error": str(e)}), 500



@control_bp.post("/schedule")
def add_schedule():
    data = request.get_json(force=True) or {}
    for key in ("device_id", "time", "repeat", "amount"):
        if not data.get(key):
            return jsonify({"error": f"{key} required"}), 400

    sid = uuid.uuid4().hex[:12]
    item = {
        "id": sid,
        "device_id": data["device_id"],
        "time": data["time"],
        "repeat": data["repeat"],
        "amount": data["amount"],
        "created_at": int(time.time()),
    }
    db = firestore.client()
    db.collection("schedules").document(sid).set(item)

    topic = f"aquanova/devices/{data['device_id']}/schedule/cmd"
    payload = {
        "cmd": "add_schedule",
        "id": sid,
        "time": data["time"],
        "repeat": data["repeat"],
        "amount": data["amount"]
    }
    result = _get_pub().publish(topic, json.dumps(payload), qos=1)
    print(f"[MQTT] Published to {topic} -> {payload}, result={result}")

    return jsonify({"ok": True, "id": sid, "item": item})


@control_bp.get("/schedules")
def list_schedules():
    db = firestore.client()
    docs = db.collection("schedules").stream()
    items = [doc.to_dict() for doc in docs]
    return jsonify({"items": items})


@control_bp.delete("/schedules/<sid>")
def delete_schedule(sid):
    db = firestore.client()
    doc_ref = db.collection("schedules").document(sid)
    if doc_ref.get().exists:
        doc_ref.delete()
        return jsonify({"ok": True})
    return jsonify({"error": "not found"}), 404


# feed_logs/
#   ├── autoID1: {device_id, amount, timestamp, local_time}
#   ├── autoID2: {...}
# schedules/
#   ├── 7e31c2d4ab12: {id, device_id, time, repeat, amount}
#   ├── 5c8f1f0a2b91: {...}
