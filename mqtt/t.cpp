@dashboard_bp.get("/summary")
def summary():
    db = firestore.client()
    ponds = db.collection("readings").stream()
    devices = db.collection("feed_logs").stream()

    pond_count = len(list(ponds))
    device_count = len(list(devices))

    return jsonify({
        "ponds": pond_count,
        "devices": device_count
    })

