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

@control_bp.post("/mode")
def set_mode():
    data = request.get_json(force=True) or {}

    mode = data.get("mode")

    if mode not in (0, 1, 2):
        return jsonify({
            "error": "mode must be 0 (normal), 1 (shift) or 2 (blink)"
        }), 40

    payload = {
        "mode": int(mode)
    }

    # ---- SEND TO NODE-RED ----
    try:
        requests.post(
            f"{NODE_RED_BASE}/cmd/mode",
            json=payload,
            timeout=2
        )
    except Exception as e:
        return jsonify({"error": f"Node-RED error: {e}"}), 502

    return jsonify(ok=True, **payload)

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
        "time": firestore.SERVER_TIMESTAMP
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

    schedule_doc = {
        "id": sid,
        "date": data["date"],
        "time": data["time"],
        "repeat": data["repeat"],
        "amount": int(data.get("amount", 20)),
        "source": "web",
        "created_at": firestore.SERVER_TIMESTAMP
    }

    ref.set(schedule_doc)

    try:
        requests.post(
        f"{NODE_RED_BASE}/cmd/schedule",
        json={
            "time": data["time"]
        },
        timeout=2
    )
    except Exception as e:
        # Không fail request nếu MQTT lỗi
        print("Node-RED schedule notify failed:", e)

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
    items = [{**d.to_dict(), "id": d.id} for d in docs]
    return jsonify(items=items)


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
    db = firestore.client()
    ref = db.collection("schedules").document(sid)
    doc = ref.get()
    if not doc.exists:
        return jsonify({"error": "Not found"}), 404

    print(">>> DELETE HIT", sid, flush=True)
    print(">>> NODE_RED_BASE =", NODE_RED_BASE, flush=True)

    r = requests.post(
        f"{NODE_RED_BASE}/cmd/delete",
        json={"delete": 1},
        timeout=3
    )
    print(">>> NODE-RED STATUS =", r.status_code, flush=True)


    ref.delete()

    return jsonify(ok=True, id=sid)


# =========================================================
# 8. DELETE FIRST SCHEDULE (DEBUG)
# =========================================================
@control_bp.delete("hook/schedule/latest")
def delete_latest_hook():
    db = firestore.client()

    docs = (
        db.collection("schedules")
        .order_by("created_at", direction=firestore.Query.DESCENDING)
        .limit(1)
        .stream()
    )

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

    status_raw = data.get("status")
    time_val = data.get("time")

    # ---------------- VALIDATE ----------------
    if not time_val or status_raw is None:
        return jsonify({"error": "missing time or status"}), 400

    # ---------------- NORMALIZE STATUS ----------------
    if isinstance(status_raw, str):
        status_norm = 1 if status_raw.upper() == "ON" else 0
    elif isinstance(status_raw, (int, float)):
        status_norm = 1 if int(status_raw) == 1 else 0
    else:
        return jsonify({"error": "invalid status type"}), 400

    # ---------------- SAVE TO FIREBASE ----------------
    ref = firestore.client().collection("feed_logs").add({
        "status": status_norm,                 # 1 = ON, 0 = OFF
        "time": str(time_val),
        "status_text": "ON" if status_norm else "OFF",
        "source": data.get("source", "mqtt"),
        "created_at": firestore.SERVER_TIMESTAMP
    })

    return jsonify(ok=True, id=ref[1].id)
# =========================================================
# 10. READ FEED LOGS (WEB → FIRESTORE)
# =========================================================
@control_bp.get("/feed-logs")
def get_feed_logs():
    limit = int(request.args.get("limit", 20))
    db = firestore.client()

    docs = (
        db.collection("feed_logs")
        .order_by("time", direction=firestore.Query.DESCENDING)
        .limit(limit)
        .stream()
    )

    items = []

    for d in docs:
        data = d.to_dict()
        ts = data.get("time")

        # ----------------------------
        # NORMALIZE TIME → day
        # ----------------------------
        if hasattr(ts, "isoformat"):
            day = ts.isoformat()
        elif isinstance(ts, str):
            day = ts
        else:
            day = None

        items.append({
            "id": d.id,
            "feed": data.get("feed", 0),
            "day": day          # ⬅️ THAY source → day
        })

    return jsonify(items=items)


