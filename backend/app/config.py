import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "dev")

    # Firebase
    FIREBASE_CREDENTIALS = os.getenv("FIREBASE_CREDENTIALS")
    FIREBASE_DB = os.getenv("FIREBASE_DB", "firestore")

    # MQTT (ĐỒNG BỘ THEO .env)
    MQTT_HOST = os.getenv("MQTT_BROKER")          # ← QUAN TRỌNG
    MQTT_PORT = int(os.getenv("MQTT_PORT", "8883"))
    MQTT_USER = os.getenv("MQTT_USERNAME")
    MQTT_PASS = os.getenv("MQTT_PASSWORD")
    MQTT_TOPIC = os.getenv("MQTT_TOPIC")

    # Background
    DISABLE_BACKGROUND = os.getenv("DISABLE_BACKGROUND", "false").lower() == "true"
