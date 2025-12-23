import os
import logging

import firebase_admin
from firebase_admin import credentials


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
    Init Firebase Admin SDK
    Chỉ khởi tạo 1 lần cho toàn bộ Flask app
    """
    if firebase_admin._apps:
        logger.info("Firebase already initialized, skip.")
        return

    cred_path = os.getenv("FIREBASE_CREDENTIALS")
    if not cred_path:
        raise RuntimeError("FIREBASE_CREDENTIALS environment variable not set")

    if not os.path.exists(cred_path):
        raise RuntimeError(f"Firebase credential file not found: {cred_path}")

    cred = credentials.Certificate(cred_path)
    firebase_admin.initialize_app(cred)

    logger.info("Firebase initialized successfully.")


def init_extensions(app):
    init_firebase(app)
