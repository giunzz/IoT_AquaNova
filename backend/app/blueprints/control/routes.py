from flask import Blueprint, jsonify, request
import requests
from firebase_admin import firestore

control_bp = Blueprint("control_bp", __name__)
NODE_RED_BASE = "http://127.0.0.1:1880"

# =========================================================
# 1. LIGHT CONTROL (WEB → NODE-RED → MQTT)
# =========================================================
@control_bp.post("/light")
def toggle_light():
    data = request.get_json(force=True) or {}

    try:
        requests.post(
            f"{NODE_RED_BASE}/cmd/light",
            json=data,
            timeout=2
        )
    except Exception as e:
        return jsonify({"error": f"Node-RED error: {e}"}), 502

    light_val = int(data.get("light", 0))
    color = data.get("color")

    firestore.client().collection("device_state").document("light").set({
        "state": light_val,
        "color": color if light_val else None,
        "updated_at": firestore.SERVER_TIMESTAMP
    })

    return jsonify(ok=True, **data)


@control_bp.get("/light")
def get_light_state():
    doc = firestore.client().collection("device_state").document("light").get()
    return jsonify(ok=True, light=doc.to_dict().get("state", 0) if doc.exists else 0)


# =========================================================
# 2. FEED NOW (WEB → NODE-RED → MQTT)
# =========================================================
@control_bp.post("/feed-now")
def feed_now():
    try:
        requests.post(
            f"{NODE_RED_BASE}/cmd/feed-now",
            json=request.get_json(force=True) or {},
            timeout=2
        )
    except Exception as e:
        return jsonify({"error": f"Node-RED error: {e}"}), 502

    firestore.client().collection("feed_logs").add({
        "feed": 1,
        "source": "manual",
        "created_at": firestore.SERVER_TIMESTAMP
    })

    return jsonify(ok=True)


# =========================================================
# 3. SCHEDULE – WEB → FIRESTORE (❗KHÔNG GỌI NODE-RED)
# =========================================================
@control_bp.post("/schedule")
def add_schedule_from_web():
    data = request.get_json(force=True) or {}

    for k in ("date", "time", "repeat"):
        if not data.get(k):
            return jsonify({"error": f"{k} required"}), 400

    sid = f"{data['date']}_{data['time']}"
    ref = firestore.client().collection("schedules").document(sid)

    if ref.get().exists:
        return jsonify({"error": "Schedule already exists"}), 409

    ref.set({
        "id": sid,
        "date": data["date"],
        "time": data["time"],
        "repeat": data["repeat"],
        "amount": int(data.get("amount", 20)),
        "source": "web",
        "created_at": firestore.SERVER_TIMESTAMP
    })

    return jsonify(ok=True, id=sid)


# =========================================================
# 4. SCHEDULE – MQTT / NODE-RED CALLBACK → FIRESTORE
# =========================================================
@control_bp.post("/hook/schedule")
def save_schedule_from_mqtt():
    data = request.get_json(force=True) or {}

    date, time_ = data.get("date"), data.get("time")
    if not date or not time_:
        return jsonify({"error": "date & time required"}), 400

    sid = f"{date}_{time_}"
    ref = firestore.client().collection("schedules").document(sid)

    if ref.get().exists:
        return jsonify({"error": "Schedule already exists"}), 409

    ref.set({
        "id": sid,
        "date": date,
        "time": time_,
        "repeat": data.get("repeat", "none"),
        "amount": int(data.get("amount", 20)),
        "source": data.get("source", "mqtt"),
        "created_at": firestore.SERVER_TIMESTAMP
    })

    return jsonify(ok=True, id=sid)


# =========================================================
# 5. READ SCHEDULES
# =========================================================
@control_bp.get("/schedules")
def list_schedules():
    docs = firestore.client().collection("schedules").stream()
    return jsonify(items=[{**d.to_dict(), "id": d.id} for d in docs])


# =========================================================
# 6. UPDATE SCHEDULE
# =========================================================
@control_bp.put("/schedules/<sid>")
def update_schedule(sid):
    ref = firestore.client().collection("schedules").document(sid)
    if not ref.get().exists:
        return jsonify({"error": "Not found"}), 404

    data = request.get_json(force=True) or {}
    update_data = {k: v for k, v in data.items() if k in {"repeat", "amount", "enabled"}}

    if not update_data:
        return jsonify({"error": "No valid fields"}), 400

    update_data["updated_at"] = firestore.SERVER_TIMESTAMP
    ref.update(update_data)

    return jsonify(ok=True, id=sid)


# =========================================================
# 7. DELETE SCHEDULE BY ID
# =========================================================
@control_bp.delete("/schedules/<sid>")
def delete_schedule(sid):
    ref = firestore.client().collection("schedules").document(sid)
    if not ref.get().exists:
        return jsonify({"error": "Not found"}), 404

    ref.delete()
    return jsonify(ok=True, id=sid)


# =========================================================
# 8. DELETE FIRST SCHEDULE (DEBUG)
# =========================================================
@control_bp.delete("/hook/schedule/latest")
def delete_first_schedule():
    docs = firestore.client().collection("schedules").stream()
    doc = next(docs, None)

    if not doc:
        return jsonify({"error": "No schedules found"}), 404

    doc.reference.delete()
    return jsonify(ok=True, deleted_id=doc.id)


# =========================================================
# 9. FEED LOG – MQTT / NODE-RED → FIRESTORE
# =========================================================
@control_bp.post("/feed-log")
def save_feed_log():
    data = request.get_json(force=True) or {}

    if data.get("feed") != 1 or not data.get("time"):
        return jsonify({"error": "invalid payload"}), 400

    ref = firestore.client().collection("feed_logs").add({
        "feed": 1,
        "time": data["time"],
        "source": data.get("source", "mqtt"),
        "created_at": firestore.SERVER_TIMESTAMP
    })

    return jsonify(ok=True, id=ref[1].id)
