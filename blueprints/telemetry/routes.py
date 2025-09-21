from flask import Blueprint, request, jsonify
from firebase_admin_init import db
from datetime import datetime

telemetry_bp = Blueprint("telemetry", __name__)

@telemetry_bp.post("/ingest")
def ingest():
    data = request.get_json(force=True)
    device_id = data.get("device_id")
    ph = data.get("ph")
    dissolved = data.get("do")
    temp = data.get("temp")

    if not device_id:
        return jsonify({"error": "device_id required"}), 400

    doc = {
        "deviceId": device_id,
        "ts": datetime.utcnow().isoformat(),
        "ph": ph, "do": dissolved, "temp": temp
    }
    db.collection("readings").add(doc)
    return jsonify({"ok": True})
