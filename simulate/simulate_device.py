import os, sys, time, random, threading
from datetime import datetime, timezone
import requests

API_URL = os.environ.get("AQUANOVA_API", "http://127.0.0.1:5000/telemetry/ingest")
API_TIMEOUT_SEC = 5

def gen_reading(device_id: str) -> dict:
    """Tạo payload mô phỏng."""
    return {
        "device_id": device_id,
        "ts": datetime.now(timezone.utc).isoformat(),   # API thường nhận ISO string
        "temperature": round(random.uniform(24.0, 31.0), 2),  # °C
        "turbidity":  round(random.uniform(10.0, 80.0), 2),   # NTU / %
        "feed":       round(random.uniform(0, 100), 1),       # % còn lại (0–100)
    }

def send_device(device_id: str, every_sec: float = 5, total: int = 5, jitter: float = 0.3):
    """
    Gửi dữ liệu từ 1 thiết bị theo chu kỳ.
    jitter: thêm trễ ngẫu nhiên ±jitter*every_sec để tránh trùng nhịp.
    """
    with requests.Session() as s:
        for i in range(total):
            payload = gen_reading(device_id)
            try:
                r = s.post(API_URL, json=payload, timeout=API_TIMEOUT_SEC)
                r.raise_for_status()
                print(f"[OK] {device_id} -> T={payload['temperature']}°C, "
                      f"Turb={payload['turbidity']}, Feed={payload['feed']}%  ({payload['ts']})")
            except Exception as e:
                print(f"[ERR] {device_id}: {e}")

            # sleep with jitter
            base = float(every_sec)
            dv = base * jitter
            time.sleep(random.uniform(max(0.1, base - dv), base + dv))

def main():
    """
    Cách chạy:
      # 3 thiết bị song song, mỗi 3s, 40 mẫu
    """
    argv = sys.argv[1:]
    devices_arg = argv[0] if len(argv) > 0 else "sensor-1"
    every = float(argv[1]) if len(argv) > 1 else 5
    total = int(argv[2]) if len(argv) > 2 else 30

    devices = [d.strip() for d in devices_arg.split(",") if d.strip()]
    if not devices:
        devices = ["sensor-1"]

    print(f"API_URL = {API_URL}")
    print(f"Devices = {devices} | every = {every}s | total = {total}")

    threads = []
    # khởi động lệch pha một chút cho tự nhiên
    for idx, dev in enumerate(devices):
        t = threading.Thread(target=send_device, args=(dev, every, total), daemon=True)
        threads.append(t)
        t.start()
        time.sleep(0.2 + 0.1 * idx)

    # chờ tất cả xong
    for t in threads:
        t.join()

if __name__ == "__main__":
    main()
