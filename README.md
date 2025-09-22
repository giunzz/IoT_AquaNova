# IoT_AquaNova
IoT project


### Cấu trúc dự án 

```
aquanova/
├─ app.py
├─ config.py
├─ firebase_admin_init.py
├─ serviceAccount.json
├─ requirements.txt
├─ .env                         # đường dẫn service account
├─ blueprints/
│  ├─ telemetry/
│  │   └─ routes.py            # nhận dữ liệu cảm biến
│  ├─ control/
│  │   └─ routes.py            # lệnh cho ăn / lịch cho ăn
│  ├─ admin/
│  │   └─ routes.py            # tạo ao, thiết bị
│  └─ dashboard/
│      └─ routes.py            # API cung cấp dữ liệu cho FE
└─ static/
   ├─ css/
   │   └─ styles.css
   └─ js/
      └─ dashboard.js
└─ templates/
   ├─ index.html                # dashboard đơn giản
   └─ admin.html                # form tạo ao / thiết bị
   ├─ temperature.html                # dashboard đơn giản
   ├─ turbidity.html                # dashboard đơn giản
   ├─ feedtimer.html                # dashboard đơn giản
└─ mqtt/
   ├─ __init__.html                
   └─ listener.html               
```
![alt text](image.png)
Device → MQTT Broker → Flask Subscriber → Firestore → Dashboard