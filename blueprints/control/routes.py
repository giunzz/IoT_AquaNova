from flask import Blueprint, request, jsonify
from firebase_admin_init import db
from datetime import datetime

control_bp = Blueprint("control", __name__)

@control_bp.post("/feed-now")
def feed_now():
    feeder_id = request.json.get("feeder_id")
    portion_g = int(request.json.get("portion_g", 100))
    if not feeder_id:
        return jsonify({"error":"feeder_id required"}), 400

    event = {
        "feederId": feeder_id,
        "ts": datetime.utcnow().isoformat(),
        "portion_g": portion_g,
        "status": "queued"
    }
    db.collection("feed_events").add(event)
    # Tùy bạn: đẩy lệnh tới thiết bị qua MQTT/HTTP ở một worker khác
    return jsonify({"ok": True})
