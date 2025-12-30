from flask import Blueprint, request, jsonify
from datetime import datetime
from firebase_admin_init import get_db

telemetry_bp = Blueprint("telemetry", __name__)
from datetime import datetime

def normalize_schedule_time(val):
    if not isinstance(val, str):
        return None

    v = val.strip().upper()
    if v == "NOT SET":
        return None

    try:
        # HH:MM:SS → HH:MM
        if v.count(":") == 2:
            return datetime.strptime(v, "%H:%M:%S").strftime("%H:%M")
        # HH:MM
        if v.count(":") == 1:
            return datetime.strptime(v, "%H:%M").strftime("%H:%M")
    except ValueError:
        return None

    return None

@telemetry_bp.post("/ingest")
def ingest_telemetry():
    data = request.get_json(force=True) or {}

    # ---------------- VALIDATE ----------------
    try:
        turbidity = float(data.get("turbidity"))
        temperature = float(data.get("temperature"))
        feed_level = float(data.get("feed_level"))
    except (TypeError, ValueError):
        return jsonify({"error": "invalid numeric fields"}), 400

    raw_schedule = data.get("schedule")
    schedule_time = normalize_schedule_time(raw_schedule)

    db = get_db()
    now = datetime.now()
    today = now.strftime("%Y-%m-%d")

    # ---------------- SAVE READING (LUÔN LUÔN) ----------------
    reading_doc = {
        "turbidity": turbidity,
        "temperature": temperature,
        "feed_level": feed_level,
        "schedule": raw_schedule,   # giữ nguyên chuỗi gốc
        "time": schedule_time,      # normalize để tiện query
        "ts": datetime.utcnow()
    }
    ref = db.collection("readings").add(reading_doc)

    # ---------------- SAVE SCHEDULE (CHỈ KHI CÓ) ----------------
    if schedule_time:
        sid = f"{today}_{schedule_time}"

        schedule_doc = {
            "id": sid,
            "date": today,
            "time": schedule_time,
            "repeat": "none",
            "amount": 20,
            "source": "telemetry",
            "created_at": datetime.utcnow()
        }

        db.collection("schedules").document(sid).set(
            schedule_doc, merge=True
        )

    return jsonify({
        "ok": True,
        "reading_id": ref[1].id,
        "schedule_saved": bool(schedule_time)
    })
