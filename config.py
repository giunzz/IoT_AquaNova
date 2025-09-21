import os
from dotenv import load_dotenv
load_dotenv()

class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "dev")

    # Firebase
    FIREBASE_CREDENTIALS = os.getenv("FIREBASE_CREDENTIALS")
    FIREBASE_DB = os.getenv("FIREBASE_DB", "firestore")

    # MQTT
    MQTT_HOST = os.getenv("MQTT_HOST", "localhost")
    MQTT_PORT = int(os.getenv("MQTT_PORT", "1883"))
    MQTT_USER = os.getenv("MQTT_USER", "")          # optional
    MQTT_PASS = os.getenv("MQTT_PASS", "")          # optional
    MQTT_TOPIC = os.getenv("MQTT_TOPIC", "aquanova/devices/+/telemetry")
