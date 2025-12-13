# IoT_AquaNova

AquaNova là hệ thống IoT giám sát và điều khiển ao nuôi cá, tích hợp:

![alt text](/img/overal.png)

- MCU (STM32, ESP32)
- MQTT (HiveMQ Cloud)
- Flask Backend (Blueprint)
- Firebase Firestore
- Web Dashboard (HTML/CSS/JS)
- Mobile App (React Native) gọi API backend

Website: https://aquanova.space

Chaỵ local back end flask (đổi api ip máy)

App test expo go: chi tiết folder aquanov_expo

---

## Demo giao diện

Dashboard:

![Dashboard](/img/image-1.png)

## Demo MCU

![MCU](/img/image.png)

---

## Kiến trúc hệ thống

Luồng dữ liệu cảm biến:

```
STM32 -> ESP32  ->  MQTT Broker  ->  Flask Subscriber  ->  Firestore  ->  Dashboard / App
```

Luồng điều khiển thiết bị (chuẩn ACK, chống lệch trạng thái):

```
Web/App
  -> POST /control/light  (gửi lệnh)
Backend publish MQTT command
  -> ESP32 đổi trạng thái relay
ESP32 -> publish ACK (light_state)
Backend (MQTT listener) -> update Firestore (device_state/light)
Web/App -> GET /control/light (đọc trạng thái thật)
```

Nguyên tắc:
- Firestore phản ánh **trạng thái thật** của thiết bị.
- Backend **chỉ** update Firestore khi nhận ACK từ ESP32.

---

## Cấu trúc dự án

```
backend/
├─ app/
│  ├─ __init__.py
│  ├─ config.py                  # Config đọc .env
│  ├─ extensions.py              # Init Firebase, MQTT, Scheduler
│  ├─ blueprints/
│  │  ├─ telemetry/
│  │  │  └─ routes.py            # API dữ liệu cảm biến
│  │  ├─ control/
│  │  │  ├─ routes.py            # Điều khiển đèn, cho ăn
│  │  │  └─ scheduler.py         # Lịch cho ăn tự động
│  │  ├─ dashboard/
│  │  │  └─ routes.py            # API dashboard
│  │  ├─ admin/
│  │  │  └─ routes.py
│  │  └─ chatbot/
│  │     └─ routes.py
│  ├─ mqtt/
│  │  ├─ __init__.py
│  │  ├─ listener.py             # MQTT subscriber (ACK, telemetry)
│  │  └─ publisher.py            # MQTT publisher (command)
│  └─ templates/                 # Jinja templates
│     ├─ layout.html
│     ├─ index.html
│     ├─ admin.html
│     ├─ temperature.html
│     ├─ turbidity.html
│     ├─ feedtimer.html
│     └─ chatbot.html
├─ static/
│  ├─ css/
│  │  └─ styles.css
│  ├─ js/
│  │  └─ dashboard.js
│  └─ img/
├─ firebase_admin_init.py
├─ app.py                        # Entry point
├─ requirements.txt
├─ serviceAccount.json
├─ .env
└─ README.md
```

---

## Cài đặt và chạy local (Windows)

### 1) Tạo môi trường ảo

```bash
cd backend
python -m venv env
env\Scripts\activate
```

### 2) Cài dependencies

```bash
pip install -r requirements.txt
```

### 3) Tạo file .env

Tạo `backend/.env` theo mẫu ở mục “Cấu hình môi trường”.

### 4) Chạy server

```bash
python app.py
```

Mở:
- http://127.0.0.1:5000

---

## Cấu hình môi trường (.env)

Ví dụ `backend/.env`:

```env
# Firebase
FIREBASE_CREDENTIALS=C:\path\to\serviceAccount.json
FIREBASE_DB=firestore
SECRET_KEY=AquaNovaSecret123

# MQTT (HiveMQ Cloud)
MQTT_BROKER=xxxx.s1.eu.hivemq.cloud
MQTT_PORT=8883
MQTT_USERNAME=your_user
MQTT_PASSWORD=your_password
MQTT_TOPIC=aquanova/telemetry

# AI
GROQ_API_KEY=your_key

# Background
DISABLE_BACKGROUND=false
```

Ghi chú:
- Không commit `.env` và `serviceAccount.json` lên GitHub.
- Khi deploy (Render/AWS), dùng “Environment Variables” thay vì hard-code.

---

## Một số API chính

Các route có thể khác tùy code hiện tại, đây là nhóm endpoint phổ biến:

- Telemetry:
  - `GET /dashboard/latest?n=60`
  - `GET /dashboard/last`
  - `GET /dashboard/announce-count`

- Control:
  - `POST /control/light` body: `{ "light": 0 | 1 }`
  - `GET /control/light` trả: `{ "light": 0 | 1 }` (đọc state từ Firestore)
  - `POST /control/feed-now`
  - `POST /control/schedule`
  - `GET /control/schedules`
  - `DELETE /control/schedules/<sid>`

---

## Đồng bộ trạng thái đèn giữa Web và App (không lệch)

Yêu cầu:
- ESP32 publish ACK sau khi đổi relay, ví dụ topic `aquanova/ack/light` với payload:
  - `{ "device": "light", "state": 0|1, "ts": ... }`

Backend:
- MQTT listener subscribe ACK topic.
- Khi nhận ACK hợp lệ, update Firestore: `device_state/light.state = 0|1`.

Web/App:
- Khi mở app/web: gọi `GET /control/light` để hiển thị trạng thái hiện tại.
- Không update UI “theo click” trước khi có ACK.

---

## Deploy trên AWS EC2

### Service quản lý bằng systemd

- Xem log:

```bash
sudo journalctl -u aquanova --no-pager
```

- Restart service:

```bash
sudo systemctl restart aquanova
sudo systemctl status aquanova
```

### Cập nhật serviceAccount.json

```bash
sudo nano /home/ec2-user/IoT_AquaNova/serviceAccount.json
```

Lưu nhanh trong nano:
- Ctrl + O -> Enter
- Ctrl + X

---

## Domain và SSL (GoDaddy + Nginx + Certbot)

Khi AWS đổi public IP:
1. Cập nhật bản ghi DNS (A record) trên GoDaddy theo IP mới
2. Chạy lại certbot:

```bash
sudo certbot --nginx -d aquanova.space -d www.aquanova.space
sudo systemctl restart aquanova
sudo systemctl status aquanova
```

---

## Deploy trên Render (gợi ý)

Nếu bạn deploy Flask lên Render:
- Runtime: Python
- Build command:

```bash
pip install -r requirements.txt
```

- Start command (ví dụ):

```bash
gunicorn app:app
```

Hoặc nếu bạn dùng factory `create_app()`:
```bash
gunicorn "app:create_app()"
```

Khuyến nghị:
- Đặt biến môi trường trên Render dashboard (FIREBASE_CREDENTIALS, MQTT_*, GROQ_API_KEY, DISABLE_BACKGROUND).
- Với `serviceAccount.json`: nên lưu dạng “secret file” (nếu có) hoặc convert sang JSON string env và load từ env (tùy cách bạn chọn).

---

## Troubleshooting

### 1) MQTT_BROKER not configured
- Lỗi do thiếu biến môi trường `MQTT_BROKER` hoặc config đọc sai key.
- Kiểm tra `.env` và `config.py` mapping.

### 2) Invalid host (MQTT)
- `MQTT_BROKER`/`MQTT_HOST` bị rỗng/None hoặc có tiền tố `https://`.
- Host phải là dạng: `xxxx.s1.eu.hivemq.cloud`

### 3) jinja2.exceptions.TemplateNotFound
- Đảm bảo `template_folder="templates"` và file nằm đúng `backend/templates/`.
- Đảm bảo chạy từ đúng working directory: `cd backend` rồi mới `python app.py`.

- Config khi AWS đổi public ip 
   - Sửa trên  godady với Ip tương ứng 
   ![alt text](/backend/app/static/img/ip.png)
   - AWs gõ 
---

## Nhóm thực hiện

- Hoàng Ngọc Dung – 23139006
- Đoàn Minh Duy Bình – 23139005
- Trần Hữu Dương – 23130009
