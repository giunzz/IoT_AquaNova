# simulate_hybrid.py
import requests, random, time, os, sys
from datetime import datetime, timezone

# --- cấu hình ---
API_URL = os.environ.get("AQUANOVA_API", "http://127.0.0.1:5000/telemetry/ingest")
FIREBASE_CRED = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS") \
             or  r"C:\Users\ASUS\Documents\GitHub\IOT_AquaNova\serviceAccount.json"

USE_FIRESTORE_FALLBACK = False   # sẽ tự bật nếu API không reachable
API_FAIL_THRESHOLD = 3           # quá N lỗi liên tiếp -> chuyển Firestore
API_TIMEOUT_SEC = 5

# --- Firestore (khởi tạo lazy khi cần) ---
_fb_inited = False
def get_firestore():
    global _fb_inited, db
    if _fb_inited:
        return db
    import firebase_admin
    from firebase_admin import credentials, firestore
    cred = credentials.Certificate(FIREBASE_CRED)
    if not firebase_admin._apps:
        firebase_admin.initialize_app(cred)
    db = firestore.client()
    _fb_inited = True
    return db

def gen_reading(device_id: str):
    """Sinh dữ liệu giả lập."""
    return {
        "device_id": device_id,                                 # tên cho API
        "deviceId": device_id,                                  # tên cho Firestore
        "ts": datetime.now(timezone.utc),
        "temperature": round(random.uniform(24.0, 31.0), 2),    # °C
        "turbidity":  round(random.uniform(10.0, 80.0), 2),     # NTU/%
        "feed":       round(random.uniform(0, 100), 1),        # gram (hoặc % nếu bạn muốn)
    }

def send_via_api(session: requests.Session, payload: dict):
    """Gửi đến Flask API. Trả True nếu thành công."""
    # API thường không nhận datetime -> chuyển ts sang ISO
    body = dict(payload)
    if isinstance(body.get("ts"), datetime):
        body["ts"] = body["ts"].isoformat()
    r = session.post(API_URL, json=body, timeout=API_TIMEOUT_SEC)
    r.raise_for_status()
    return True

def send_direct_firestore(payload: dict):
    """Ghi trực tiếp Firestore."""
    db = get_firestore()
    # Chuẩn hóa field cho Firestore
    doc = {
        "deviceId": payload.get("deviceId") or payload.get("device_id"),
        "ts": payload.get("ts") or datetime.now(timezone.utc),
        "temperature": payload.get("temperature"),
        "turbidity": payload.get("turbidity"),
        "feed": payload.get("feed"),
    }
    db.collection("readings").add(doc)
    return True

def simulate(device_id="sensor-3", every_sec=5, total=30):
    global USE_FIRESTORE_FALLBACK
    consecutive_api_fail = 0
    with requests.Session() as s:
        for i in range(total):
            payload = gen_reading(device_id)
            try:
                if not USE_FIRESTORE_FALLBACK:
                    # thử API trước
                    send_via_api(s, payload)
                    consecutive_api_fail = 0
                    print(f"[API OK]  {payload['ts']} {device_id}: "
                          f"T={payload['temperature']}°C, Turb={payload['turbidity']}, Feed={payload['feed']}")
                else:
                    # đã fallback rồi -> ghi Firestore
                    send_direct_firestore(payload)
                    print(f"[FS  OK]  {payload['ts']} {device_id}: "
                          f"T={payload['temperature']}°C, Turb={payload['turbidity']}, Feed={payload['feed']}")
            except Exception as e:
                if not USE_FIRESTORE_FALLBACK:
                    consecutive_api_fail += 1
                    print(f"[API ERR {consecutive_api_fail}] {e} -> switch after {API_FAIL_THRESHOLD}")
                    if consecutive_api_fail >= API_FAIL_THRESHOLD:
                        # bật fallback
                        try:
                            get_firestore()  # init để chắc chắn hợp lệ
                            USE_FIRESTORE_FALLBACK = True
                            print("[INFO] Switching to Firestore direct write.")
                            send_direct_firestore(payload)
                            print(f"[FS  OK]  {payload['ts']} {device_id}: "
                                  f"T={payload['temperature']}°C, Turb={payload['turbidity']}, Feed={payload['feed']}")
                        except Exception as e2:
                            print(f"[FATAL] Firestore init/write failed: {e2}")
                            sys.exit(1)
                else:
                    print(f"[FS ERR] {e}")
            time.sleep(every_sec)

if __name__ == "__main__":
    # Có thể truyền tham số: device_id every_sec total
    # vd: python simulate_hybrid.py sensor-1 3 50
    argv = sys.argv[1:]
    dev = argv[0] if len(argv) > 0 else "sensor-3"
    gap = int(argv[1]) if len(argv) > 1 else 5
    cnt = int(argv[2]) if len(argv) > 2 else 30
    simulate(dev, gap, cnt)
