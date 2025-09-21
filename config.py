import os
from dotenv import load_dotenv
load_dotenv()

class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "dev")
    FIREBASE_CREDENTIALS = os.getenv("FIREBASE_CREDENTIALS")  # đường dẫn file JSON service account
    FIREBASE_DB = os.getenv("FIREBASE_DB", "firestore")       # "firestore" (khuyến nghị)
