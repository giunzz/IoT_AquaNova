from flask import Blueprint, jsonify, request, current_app
from firebase_admin_init import get_db
from firebase_admin import firestore
from datetime import datetime

dashboard_bp = Blueprint("dashboard", __name__)

def _to_iso(val):
    if hasattr(val, "isoformat"):
        return val.isoformat()
    return val

@dashboard_bp.get("/latest")
def latest():
    """
    Trả về N bản ghi mới nhất (mặc định 60) để vẽ chart + bảng.
    Schema Firestore mỗi doc: { deviceId, ts(Timestamp), temperature, turbidity, feed_amount }
    """
    N = int(request.args.get("n", 60))
    db = get_db()
    q = (db.collection("readings")
            .order_by("ts", direction=firestore.Query.DESCENDING)
            .limit(N))
    items = []
    for d in q.stream():
        x = d.to_dict()
        x["id"] = d.id
        x["ts"] = _to_iso(x.get("ts"))
        items.append(x)
    return jsonify({"items": items})

@dashboard_bp.get("/last")
def last():
    """Trả về 1 bản ghi mới nhất (cho các thẻ tóm tắt)."""
    db = get_db()
    q = (db.collection("readings")
            .order_by("ts", direction=firestore.Query.DESCENDING)
            .limit(1))
    docs = list(q.stream())
    if not docs:
        return jsonify({"item": None})
    x = docs[0].to_dict()
    x["id"] = docs[0].id
    x["ts"] = _to_iso(x.get("ts"))
    return jsonify({"item": x})

@dashboard_bp.get("/announce-count")
def announce_count():
    """
    Ví dụ đếm “rủi ro” trong 60 mẫu gần nhất dựa trên ngưỡng hiển thị:
      - temperature ngoài [24, 30]  -> +1
      - turbidity  > 70 (ví dụ)     -> +1
    Bạn có thể chỉnh ngưỡng cho phù hợp.
    """
    db = get_db()
    q = (db.collection("readings")
            .order_by("ts", direction=firestore.Query.DESCENDING)
            .limit(60))
    cnt = 0
    for d in q.stream():
        r = d.to_dict()
        t = r.get("temperature")
        turb = r.get("turbidity")
        if t is not None and (t < 24 or t > 30):
            cnt += 1
        if turb is not None and turb > 70:
            cnt += 1
    return jsonify({"count": cnt})
