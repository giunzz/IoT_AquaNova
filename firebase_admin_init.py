import os
import firebase_admin
from firebase_admin import credentials, firestore
from config import Config

firebase_app = None
db = None

def init_firebase():
    global firebase_app, db
    cred_path = Config.FIREBASE_CREDENTIALS
    print(f"[Firebase Init] Using credentials: {cred_path}")

    if not cred_path or not os.path.isfile(cred_path):
        raise RuntimeError(f"Service account not found: {cred_path}")

    if not firebase_admin._apps:
        cred = credentials.Certificate(cred_path)
        firebase_app = firebase_admin.initialize_app(cred)
    db = firestore.client()
    return db

def get_db():
    global db
    if db is None:
        init_firebase()
    return db
