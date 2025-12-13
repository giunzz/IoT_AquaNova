import os
import logging

import firebase_admin
from firebase_admin import credentials

import paho.mqtt.client as mqtt
from apscheduler.schedulers.background import BackgroundScheduler


# =========================
# LOGGER
# =========================
logger = logging.getLogger("extensions")
logging.basicConfig(level=logging.INFO)


# =========================
# FIREBASE
# =========================
def init_firebase(app):
    """
    Init Firebase Admin SDK (chỉ chạy 1 lần)
    """
    if firebase_admin._apps:
        logger.info("Firebase already initialized, skip.")
        return

    cred_path = os.getenv("FIREBASE_CREDENTIALS")
    if not cred_path:
        raise RuntimeError("FIREBASE_CREDENTIALS environment variable not set")

    cred = credentials.Certificate(cred_path)
    firebase_admin.initialize_app(cred)

    logger.info("Firebase initialized successfully.")


# =========================
# MQTT
# =========================
mqtt_client = None


def init_mqtt(app):
    """
    Init MQTT client (chỉ chạy 1 lần)
    """
    global mqtt_client

    if mqtt_client is not None:
        logger.info("MQTT already initialized, skip.")
        return mqtt_client

    broker = app.config.get("MQTT_BROKER")
    port = int(app.config.get("MQTT_PORT", 1883))
    username = app.config.get("MQTT_USERNAME")
    password = app.config.get("MQTT_PASSWORD")

    if not broker:
        raise RuntimeError("MQTT_BROKER not configured")

    client = mqtt.Client()

    if username and password:
        client.username_pw_set(username, password)

    client.connect(broker, port, keepalive=60)
    client.loop_start()

    mqtt_client = client
    app.mqtt = client

    logger.info(f"MQTT connected to {broker}:{port}")
    return client


def stop_mqtt(app):
    """
    Stop MQTT cleanly
    """
    global mqtt_client

    if mqtt_client:
        mqtt_client.loop_stop()
        mqtt_client.disconnect()
        mqtt_client = None
        logger.info("MQTT stopped.")


# =========================
# SCHEDULER
# =========================
scheduler = BackgroundScheduler()


def init_scheduler(app):
    """
    Init APScheduler (chỉ start 1 lần)
    """
    if scheduler.running:
        logger.info("Scheduler already running, skip.")
        return scheduler

    scheduler.start()
    app.scheduler = scheduler

    logger.info("Scheduler started.")
    return scheduler


def shutdown_scheduler(app):
    """
    Shutdown scheduler cleanly
    """
    if scheduler.running:
        scheduler.shutdown(wait=False)
        logger.info("Scheduler stopped.")


# =========================
# MASTER INIT
# =========================
def init_extensions(app):
    # Firebase (luôn bật)
    init_firebase(app)

    # Background services (MQTT + Scheduler)
    disable_bg = app.config.get("DISABLE_BACKGROUND", False)

    if disable_bg:
        logger.warning("Background services DISABLED by config.")
        return

    # MQTT
    init_mqtt(app)

    # Scheduler
    init_scheduler(app)
