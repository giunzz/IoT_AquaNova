from flask import Blueprint, render_template, request, jsonify
from .agents import aqua_agent
chatbot_bp = Blueprint("chatbot", __name__)

@chatbot_bp.route("/")
def chatbot_page():
    return render_template("chatbot.html")

@chatbot_bp.route("/api", methods=["POST"])
def chatbot_api():
    data = request.get_json()
    msg = data.get("message", "")

    try:
        response = aqua_agent.run(msg)
        return jsonify(reply=response.content)  # JSON từ agent
    except Exception as e:
        return jsonify(reply=f"Lỗi xử lý: {str(e)}")
