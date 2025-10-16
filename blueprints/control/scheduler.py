# blueprints/control/scheduler.py
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime
from firebase_admin import firestore
import json
from .routes import _get_pub  

scheduler = BackgroundScheduler()

def check_schedules():
    db = firestore.client()
    now = datetime.now().strftime("%H:%M")

    docs = db.collection("schedules").stream()
    for doc in docs:
        data = doc.to_dict()
        if data["time"] == now:
            topic = f"aquanova/devices/{data['device_id']}/control"
            payload = {"cmd": "feed", "amount": data["amount"]}
            _get_pub().publish(topic, json.dumps(payload), qos=1)
            print(f"[SCHEDULE] Sent feed cmd to {data['device_id']} at {now}")

            db.collection("feed_logs").add({
                "device_id": data["device_id"],
                "amount": data["amount"],
                "timestamp": firestore.SERVER_TIMESTAMP,
                "from_schedule": data["id"]
            })

            if not data["repeat"]:
                db.collection("schedules").document(data["id"]).delete()

def start_scheduler():
    scheduler.add_job(check_schedules, "interval", minutes=1)
    scheduler.start()
    print(" Started checking schedules every minute")
