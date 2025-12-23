from flask import Blueprint, jsonify, request
import requests
import time
import uuid
import json

from firebase_admin import firestore


control_bp = Blueprint("control_bp", __name__)

NODE_RED_BASE = "http://127.0.0.1:1880"


@control_bp.post("/light")
def toggle_light():
    data = request.get_json(force=True) or {}

    try:
        r = requests.post(
            f"{NODE_RED_BASE}/cmd/light",
            json=data,
            timeout=3
        )
    except requests.RequestException as e:
        return jsonify({"error": f"Node-RED unreachable: {e}"}), 502

    if r.status_code != 200:
        return jsonify({"error": "Node-RED error"}), 502

    # Lưu trạng thái đèn
    light_val = int(data.get("light", 0))
    color = data.get("color")

    db = firestore.client()
    db.collection("device_state").document("light").set({
        "state": light_val,
        "color": color if light_val == 1 else None,
        "updated_at": firestore.SERVER_TIMESTAMP
    })

    return jsonify(ok=True, **data)


@control_bp.get("/light")
def get_light_state():
    db = firestore.client()
    doc = db.collection("device_state").document("light").get()

    if not doc.exists:
        return jsonify({"ok": True, "light": 0})

    data = doc.to_dict()
    return jsonify({
        "ok": True,
        "light": data.get("state", 0)
    })


@control_bp.post("/feed-now")
def feed_now():
    data = request.get_json(force=True) or {}

    r = requests.post(
        f"{NODE_RED_BASE}/cmd/feed-now",
        json=data,
        timeout=3
    )

    if r.status_code != 200:
        return jsonify({"error": "Node-RED error"}), 502

    db = firestore.client()
    db.collection("feed_logs").add({
        "timestamp": firestore.SERVER_TIMESTAMP,
        "source": "manual"
    })

    return jsonify(ok=True)


@control_bp.get("/schedules")
def list_schedules():
    db = firestore.client()

    docs = (
        db.collection("schedules")
        .order_by("date")
        .order_by("time")
        .stream()
    )

    items = []
    for d in docs:
        item = d.to_dict() or {}
        item["id"] = d.id          # <<< CỰC KỲ QUAN TRỌNG
        items.append(item)

    return jsonify(items=items)

@control_bp.post("/schedule")
def add_schedule():
    data = request.get_json(force=True) or {}

    required = ("date", "time", "repeat")
    for k in required:
        if not data.get(k):
            return jsonify({"error": f"{k} required"}), 400

    sid = f"{data['date']}_{data['time']}"

    payload = {
        "id": sid,
        "date": data["date"],
        "time": data["time"],
        "repeat": data["repeat"],
        "amount": data.get("amount", 20),
        "source": "web"
    }

    r = requests.post(
        "http://127.0.0.1:1880/cmd/schedule",
        json=payload,
        timeout=3
    )

    if r.status_code != 200:
        return jsonify({"error": "Node-RED error"}), 502

    return jsonify(ok=True, pending_id=sid)


@control_bp.post("/hook/schedule")
def save_schedule_from_mqtt():
    data = request.get_json(force=True) or {}

    date = data.get("date")
    time_ = data.get("time")

    if not date or not time_:
        return jsonify({"error": "date & time required"}), 400

    sid = f"{date}_{time_}"   # <<< CHỐT

    db = firestore.client()
    ref = db.collection("schedules").document(sid)

    if ref.get().exists:
        return jsonify({"error": "Schedule already exists"}), 409

    ref.set({
        "id": sid,
        "date": date,
        "time": time_,
        "source": "mqtt",
        "created_at": firestore.SERVER_TIMESTAMP
    })

    return jsonify(ok=True, id=sid)


@control_bp.put("/schedules/<sid>")
def update_schedule(sid):
    data = request.get_json(force=True) or {}

    db = firestore.client()
    ref = db.collection("schedules").document(sid)
    doc = ref.get()

    if not doc.exists:
        return jsonify({"error": "Not found"}), 404

    old = doc.to_dict()

    # Cấm đổi date / time (để không phá ID)
    if "date" in data or "time" in data:
        return jsonify({"error": "date/time cannot be updated"}), 400

    allowed = {"repeat", "amount", "enabled"}
    update_data = {k: v for k, v in data.items() if k in allowed}

    if not update_data:
        return jsonify({"error": "No valid fields"}), 400

    update_data["updated_at"] = firestore.SERVER_TIMESTAMP
    ref.update(update_data)

    return jsonify(ok=True, id=sid)

@control_bp.delete("/schedules/<sid>")
def delete_schedule(sid):
    db = firestore.client()
    ref = db.collection("schedules").document(sid)

    if not ref.get().exists:
        return jsonify({"error": "Not found"}), 404

    ref.delete()
    return jsonify(ok=True, id=sid)

@control_bp.delete("/hook/schedule/latest")
def delete_latest_schedule():
    db = firestore.client()

    # Lấy bản ghi mới nhất
    docs = (
        db.collection("schedules")
        .order_by("created_at", direction=firestore.Query.DESCENDING)
        .limit(1)
        .stream()
    )

    doc = None
    for d in docs:
        doc = d
        break

    if not doc:
        return jsonify({"error": "No schedules found"}), 404

    doc.reference.delete()

    return jsonify(
        ok=True,
        deleted_id=doc.id,
        deleted=doc.to_dict()
    )

