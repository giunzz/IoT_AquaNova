import json
import requests
from flask import Blueprint, render_template, request, jsonify
from .agents import aqua_agent

NODE_RED_BASE = "http://127.0.0.1:1880"   

chatbot_bp = Blueprint("chatbot", __name__)

@chatbot_bp.route("/")
def chatbot_page():
    return render_template("chatbot.html")


@chatbot_bp.route("/api", methods=["POST"])
def chatbot_api():
    data = request.get_json() or {}
    msg = data.get("message", "").lower()

    # ---------------- HARD INTENT (VIETNAMESE) ----------------
    payload = {}

    if "cho ăn" in msg or "cho ca an" in msg:
        payload["feeding"] = 1
    elif "ngưng cho ăn" in msg or "dừng cho ăn" in msg:
        payload["feeding"] = 0

    if "bật đèn" in msg or "mở đèn" in msg:
        payload["light"] = 1
    elif "tắt đèn" in msg:
        payload["light"] = 0

    # Nếu bắt được intent cứng → gửi luôn
    if payload:
        try:
            requests.post(
                f"{NODE_RED_BASE}/cmd/chatbot",
                json=payload,
                timeout=3
            )
            return jsonify(reply=f"Đã gửi lệnh: {payload}")
        except Exception as e:
            return jsonify(reply=f"Lỗi gửi lệnh: {str(e)}")

    # ---------------- FALLBACK: AGENT ----------------
    try:
        agent_resp = aqua_agent.run(msg)
        content = agent_resp.content

        try:
            parsed = json.loads(content)

            payload = {}

            if "light" in parsed:
                payload["light"] = 1 if str(parsed["light"]).upper() in ("1", "ON", "TRUE") else 0

            if "feeding" in parsed:
                payload["feeding"] = 1 if str(parsed["feeding"]).upper() in ("1", "ON", "TRUE") else 0

            if payload:
                requests.post(
                    f"{NODE_RED_BASE}/cmd/chatbot",
                    json=payload,
                    timeout=3
                )

            return jsonify(reply=content)

        except json.JSONDecodeError:
            return jsonify(reply=content)

    except Exception as e:
        return jsonify(reply=f"Lỗi xử lý: {str(e)}")
    return jsonify(reply="Xin lỗi, tôi không hiểu yêu cầu của bạn.")