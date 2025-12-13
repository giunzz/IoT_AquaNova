import os
import firebase_admin
from firebase_admin import credentials, firestore

firebase_app = None
db = None


def init_firebase():
    """
    Init Firebase Admin SDK (chỉ chạy 1 lần)
    """
    global firebase_app, db

    if firebase_admin._apps:
        db = firestore.client()
        return db

    cred_path = os.getenv("FIREBASE_CREDENTIALS")
    print(f"[Firebase Init] Using credentials: {cred_path}")

    if not cred_path or not os.path.isfile(cred_path):
        raise RuntimeError(f"Service account not found: {cred_path}")

    cred = credentials.Certificate(cred_path)
    firebase_app = firebase_admin.initialize_app(cred)
    db = firestore.client()

    return db


def get_db():
    """
    Get Firestore client (lazy init)
    """
    global db
    if db is None:
        return init_firebase()
    return db
