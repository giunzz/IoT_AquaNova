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
├─ .env                         
├─ blueprints/
│  ├─ telemetry/
│  │   └─ routes.py            
│  ├─ control/
│  │   └─ routes.py            
│  ├─ admin/
│  │   └─ routes.py            
│  └─ dashboard/
│      └─ routes.py            
└─ static/
   ├─ css/
   │   └─ styles.css
   └─ js/
      └─ dashboard.js
└─ templates/
   ├─ index.html                
   └─ admin.html                
   ├─ temperature.html                
   ├─ turbidity.html               
   ├─ feedtimer.html                
└─ mqtt/
   ├─ __init__.html                
   └─ listener.html               
```
![alt text](image.png)
Device → MQTT Broker → Flask Subscriber → Firestore → Dashboard

Xem log: sudo journalctl -u aquanova --no-pager

IP web: http://3.26.52.227


sửa code 
sudo nano /home/ec2-user/IoT_AquaNova/serviceAccount.json

CTRL K 
CTRL + O  →  Enter
CTRL + X

sudo systemctl restart aquanova
sudo systemctl status aquanova 
(xem activate)
