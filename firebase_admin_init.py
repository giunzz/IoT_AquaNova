import firebase_admin
from firebase_admin import credentials, firestore
from config import Config

firebase_app = None
db = None

def init_firebase():
    global firebase_app, db
    if not firebase_admin._apps:
        cred = credentials.Certificate(Config.FIREBASE_CREDENTIALS)
        firebase_app = firebase_admin.initialize_app(cred)
    db = firestore.client()
    return db
