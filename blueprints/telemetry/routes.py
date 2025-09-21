from flask import Blueprint, request, jsonify
from datetime import datetime
from firebase_admin_init import get_db

telemetry_bp = Blueprint("telemetry", __name__)

@telemetry_bp.post("/ingest")
def ingest():
    data = request.json or {}
    data["ts"] = datetime.utcnow()

    db = get_db()  # <-- luôn chắc chắn có db
    db.collection("readings").add(data)

    return jsonify({"status": "ok", "data": data})
