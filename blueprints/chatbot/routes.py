from flask import Blueprint, render_template, request, jsonify

chatbot_bp = Blueprint("chatbot", __name__)

@chatbot_bp.route("/")
def chatbot_page():
    return render_template("chatbot.html")

@chatbot_bp.route("/api", methods=["POST"])
def chatbot_api():
    data = request.get_json()
    msg = data.get("message", "").lower()

    # Demo xử lý lệnh giọng nói
    if "bật đèn" in msg:
        return jsonify(reply="Đèn đã bật.")

    if "tắt đèn" in msg:
        return jsonify(reply="Đèn đã tắt.")

    if "cho ăn" in msg:
        return jsonify(reply="Đang cho cá ăn…")

    return jsonify(reply=f"Tôi nhận được: {msg}")
