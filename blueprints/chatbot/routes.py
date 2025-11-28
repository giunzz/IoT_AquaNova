from flask import Blueprint, render_template, request, jsonify
from .agents import aqua_agent
import json

from ..control.routes import _get_pub  
def publish_from_agent(data: dict):
    """
    Publish MQTT nếu agent trả JSON có "light" hoặc "feeding"
    """
    if not isinstance(data, dict):
        return False

    # Chỉ publish 2 loại lệnh
    if "light" not in data and "feeding" not in data:
        return False

    topic = "aquanova/control"
    payload = json.dumps(data)

    print(f"[MQTT] Publishing {data} → {topic}")
    client = _get_pub()
    client.publish(topic, payload, qos=1)

    return True


chatbot_bp = Blueprint("chatbot", __name__)

@chatbot_bp.route("/")
def chatbot_page():
    return render_template("chatbot.html")


@chatbot_bp.route("/api", methods=["POST"])
def chatbot_api():
    data = request.get_json()
    msg = data.get("message", "")

    try:
        # Agent trả kết quả
        agent_resp = aqua_agent.run(msg)
        content = agent_resp.content

        # TH1: Agent trả JSON → điều khiển thiết bị
        try:
            parsed_json = json.loads(content)

            publish_from_agent(parsed_json)

            return jsonify(reply=json.dumps(parsed_json, ensure_ascii=False))


        except json.JSONDecodeError:
            return jsonify(reply=content)

    except Exception as e:
        return jsonify(reply=f"Lỗi xử lý: {str(e)}")
