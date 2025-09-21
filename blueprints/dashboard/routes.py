from flask import Blueprint, jsonify, request
from firebase_admin_init import db

dashboard_bp = Blueprint("dashboard", __name__)

@dashboard_bp.get("/latest")
def latest_readings():
    pond_id = request.args.get("pondId")
    q = db.collection("readings").order_by("ts", direction="DESCENDING").limit(20)
    if pond_id:
        # nếu bạn lưu device.pondId, có thể filter theo pond
        pass
    docs = [ { **d.to_dict(), "id": d.id } for d in q.stream() ]
    return jsonify({"items": docs})

@dashboard_bp.get("/summary")
def summary():
    # ví dụ trả về số ao, số thiết bị
    ponds = len(list(db.collection("ponds").stream()))
    devices = len(list(db.collection("devices").stream()))
    return jsonify({"ponds": ponds, "devices": devices})
