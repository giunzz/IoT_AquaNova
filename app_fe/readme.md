# Aquanova_app

## Cấu trúc 
AquaNova/
│── backend/
│   ├── app.py
│   ├── blueprints/
│   ├── mqtt/
│   ├── firebase_admin_init.py
│   ├── templates/ (web dashboard)
│   └── static/
│
│── aquanova_expo/
│   ├── app/ # code fe ở đây
│   ├── components/
│   ├── assets/
│   ├── package.json
│   └── app.config.js
│
└── README.md

### Cài backend
```
cd backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python app.py
```

### Cài frontend

```
cd aquanova_expo
npm install
npx expo start
```

