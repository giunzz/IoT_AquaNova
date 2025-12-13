# ============================================================
#  AquaNova Feeding Scheduler
#  Kiểm tra và gửi lệnh cho ăn định kỳ
# ============================================================

from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime, date, timedelta
from firebase_admin import firestore
import json
from .routes import _get_pub

scheduler = BackgroundScheduler()


# ------------------------------------------------------------
# Hàm kiểm tra lịch cho ăn
# ------------------------------------------------------------
def check_schedules(app):
    with app.app_context():   # đảm bảo mỗi lần chạy đều có context
        db = firestore.client()
        now = datetime.now()
        print(f"[DEBUG] Checking schedules at {now.strftime('%H:%M:%S')}")  # 👈 để debug
        db = firestore.client()
        now = datetime.now()

        # Lấy tất cả lịch trong Firestore
        docs = db.collection("schedules").stream()
        for doc in docs:
            data = doc.to_dict()
            sched_id = data.get("id")

            # Bỏ qua nếu thiếu thông tin
            sched_time = data.get("time")
            sched_date = data.get("date")
            repeat = data.get("repeat", "none")
            amount = data.get("amount", 0)

            if not sched_time:
                continue

            # So sánh giờ
            try:
                hh, mm = map(int, sched_time.split(":"))
            except ValueError:
                continue

            # Nếu có date → chỉ chạy khi ngày khớp hoặc repeat cho phép
            today_str = now.strftime("%Y-%m-%d")

            # Kiểm tra thời gian hiện tại có khớp lịch không
            # (cho phép sai lệch ±60 giây để tránh miss)
            is_time_match = (
                now.hour == hh and now.minute == mm and abs(now.second) < 60
            )

            if not is_time_match:
                continue

            # Kiểm tra theo loại repeat
            run = False
            if repeat == "none":
                if sched_date == today_str:
                    run = True
            elif repeat == "daily":
                run = True
            elif repeat == "weekly":
                try:
                    sched_dt = datetime.strptime(sched_date, "%Y-%m-%d").date()
                    if now.date().weekday() == sched_dt.weekday():
                        run = True
                except Exception:
                    pass

            if not run:
                continue

            # ---- Thực thi lệnh cho ăn ----
            topic = "aquanova/control"
            payload = {"feeding": 1}
            print(f"[SCHEDULE] Feed → {topic} (repeat={repeat})")

            try:
                _get_pub().publish(topic, json.dumps(payload), qos=1)
                print(f"[SCHEDULE] Published feed successfully.")
            except Exception as e:
                print(f"[ERROR] Failed to publish feed schedule: {e}")

            # Ghi log vào Firestore
            db.collection("feed_logs").add({
                "timestamp": firestore.SERVER_TIMESTAMP,
            })

            # Nếu repeat = none → xóa sau khi thực hiện
            if repeat == "none":
                db.collection("schedules").document(sched_id).delete()
                print(f"[SCHEDULE] Deleted one-time schedule {sched_id}")

def start_scheduler(app):
    scheduler.add_job(
        check_schedules,
        "interval",
        minutes=1,
        args=[app],   # truyền app vào job
        max_instances=1,
        coalesce=True
    )
    scheduler.start()
    print("[Scheduler] Started — checking schedules every minute")
