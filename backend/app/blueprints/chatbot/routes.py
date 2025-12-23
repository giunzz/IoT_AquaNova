import json
import requests
from flask import Blueprint, render_template, request, jsonify
from .agents import aqua_agent

NODE_RED_BASE = "http://127.0.0.1:1880"   # hoặc IP EC2

chatbot_bp = Blueprint("chatbot", __name__)

@chatbot_bp.route("/")
def chatbot_page():
    return render_template("chatbot.html")


@chatbot_bp.route("/api", methods=["POST"])
def chatbot_api():
    data = request.get_json() or {}
    msg = data.get("message", "")

    try:
        agent_resp = aqua_agent.run(msg)
        content = agent_resp.content

        try:
            parsed = json.loads(content)

            if "light" in parsed or "feeding" in parsed:
                requests.post(
                    f"{NODE_RED_BASE}/cmd/chatbot",
                    json=parsed,
                    timeout=3
                )

            return jsonify(reply=content)

        except json.JSONDecodeError:
            return jsonify(reply=content)

    except Exception as e:
        return jsonify(reply=f"Lỗi xử lý: {str(e)}")
