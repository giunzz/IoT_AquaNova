from flask import Blueprint, jsonify, request
from firebase_admin import firestore

dashboard_bp = Blueprint("dashboard", __name__)

# ------------------------------------------------------------
# Lấy nhiều bản ghi mới nhất
# ------------------------------------------------------------
@dashboard_bp.get("/latest")
def latest():
    n = int(request.args.get("n", 100))
    db = firestore.client()
    docs = (
        db.collection("readings")
        .order_by("ts", direction=firestore.Query.DESCENDING)
        .limit(n)
        .stream()
    )
    items = []
    for doc in docs:
        d = doc.to_dict()
        items.append({
            "ts": d.get("ts"),
            "temperature": d.get("temperature"),
            "turbidity": d.get("turbidity"),
            "feed": d.get("feed"),
            "thoi_gian": d.get("thoi_gian")
        })
    return jsonify({"items": items})


# ------------------------------------------------------------
# Lấy 1 bản ghi mới nhất (dùng cho card Feed Amount)
# ------------------------------------------------------------
@dashboard_bp.get("/last")
def last():
    db = firestore.client()
    q = (
        db.collection("readings")
        .order_by("ts", direction=firestore.Query.DESCENDING)
        .limit(1)
    )
    docs = list(q.stream())
    if not docs:
        return jsonify({"item": None})
    x = docs[0].to_dict()
    x["id"] = docs[0].id
    return jsonify({"item": x})


# ------------------------------------------------------------
# Đếm số bản ghi bất thường (cảnh báo)
# ------------------------------------------------------------
@dashboard_bp.get("/announce-count")
def announce_count():
    db = firestore.client()
    q = (
        db.collection("readings")
        .order_by("ts", direction=firestore.Query.DESCENDING)
        .limit(60)
    )
    cnt = 0
    for d in q.stream():
        r = d.to_dict()
        t = r.get("temperature")
        turb = r.get("turbidity")
        if t is not None and (t < 24 or t > 30):
            cnt += 1
        if turb is not None and turb > 1000:
            cnt += 1
    return jsonify({"count": cnt})
