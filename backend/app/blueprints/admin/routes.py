from flask import Blueprint, request, jsonify
from firebase_admin_init import get_db

admin_bp = Blueprint("admin", __name__)


@admin_bp.post("/ponds")
def create_pond():
    db = get_db()   # 
    doc = request.get_json(force=True)
    ref = db.collection("ponds").add(doc)
    return jsonify({"id": ref[1].id, "ok": True})

@admin_bp.post("/devices")
def create_device():
    db = get_db()   
    doc = request.get_json(force=True)
    ref = db.collection("devices").add(doc)
    return jsonify({"id": ref[1].id, "ok": True})
