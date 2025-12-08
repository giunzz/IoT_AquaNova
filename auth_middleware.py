from functools import wraps
from flask import request, jsonify, redirect, url_for
from firebase_admin import auth, firestore

db = firestore.client()

def verify_token(id_token):
    try:
        decoded = auth.verify_id_token(id_token)
        return decoded
    except:
        return None


def auth_required(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        id_token = None

        # 1. Lấy từ cookie (khuyên dùng)
        if "idToken" in request.cookies:
            id_token = request.cookies.get("idToken")

        # 2. Hoặc client gửi qua header
        if not id_token and "Authorization" in request.headers:
            bearer = request.headers.get("Authorization")
            if bearer.startswith("Bearer "):
                id_token = bearer.split(" ")[1]

        if not id_token:
            return redirect(url_for("dashboard.login_page"))

        decoded = verify_token(id_token)
        if not decoded:
            return redirect(url_for("dashboard.login_page"))

        request.user = decoded
        return func(*args, **kwargs)
    return wrapper


def role_required(required_role):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            user = request.user
            uid = user["uid"]

            doc = db.collection("users").document(uid).get()
            role = "user"
            if doc.exists:
                role = doc.to_dict().get("role", "user")

            if role != required_role:
                return "Permission denied", 403

            return func(*args, **kwargs)
        return wrapper
    return decorator
