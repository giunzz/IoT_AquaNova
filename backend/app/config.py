import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "dev")

    # =====================
    # Firebase
    # =====================
    FIREBASE_CREDENTIALS = os.getenv("FIREBASE_CREDENTIALS")
    FIREBASE_DB = os.getenv("FIREBASE_DB", "firestore")

    # =====================
    # MQTT (CHUẨN TÊN)
    # =====================
    MQTT_BROKER = os.getenv("MQTT_BROKER")
    MQTT_PORT = int(os.getenv("MQTT_PORT", "1883"))
    MQTT_USERNAME = os.getenv("MQTT_USERNAME", "")
    MQTT_PASSWORD = os.getenv("MQTT_PASSWORD", "")
    MQTT_TOPIC = os.getenv("MQTT_TOPIC", "aquanova/devices/+/telemetry")

    # =====================
    # Background services
    # =====================
    DISABLE_BACKGROUND = os.getenv("DISABLE_BACKGROUND", "false").lower() == "true"
