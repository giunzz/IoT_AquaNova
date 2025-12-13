from flask import Flask, render_template, jsonify
from flask_cors import CORS

from .config import Config
from .extensions import init_extensions

from .blueprints.telemetry.routes import telemetry_bp
from .blueprints.control.routes import control_bp
from .blueprints.admin.routes import admin_bp
from .blueprints.dashboard.routes import dashboard_bp
from .blueprints.chatbot.routes import chatbot_bp


def create_app():
    app = Flask(
        __name__,
        static_folder="static",
        template_folder="templates"
    )
    app.config.from_object(Config)

    # CORS: cho Expo/React gọi API
    # Nếu muốn chặt hơn, set origins theo app.config
    CORS(
        app,
        resources={r"/*": {"origins": "*"}},
        supports_credentials=False
    )

    # Init Firebase/MQTT/Scheduler
    init_extensions(app)

    # ===== API blueprints =====
    app.register_blueprint(telemetry_bp, url_prefix="/telemetry")
    app.register_blueprint(control_bp, url_prefix="/control")
    app.register_blueprint(admin_bp, url_prefix="/admin")
    app.register_blueprint(dashboard_bp, url_prefix="/dashboard")
    app.register_blueprint(chatbot_bp, url_prefix="/chatbot")


    # ===== Health check cho FE test =====
    @app.get("/api/health")
    def api_health():
        return jsonify({"ok": True, "service": "AquaNova Backend"})

    # ===== Web routes (templates) =====
    @app.get("/")
    def home():
        return render_template("index.html")

    @app.get("/admin-page")
    def admin_page():
        return render_template("admin.html")

    @app.get("/temperature")
    def temperature_page():
        return render_template("temperature.html")

    @app.get("/turbidity")
    def turbidity_page():
        return render_template("turbidity.html")

    @app.get("/feedtimer")
    def feed_timer_page():
        return render_template("feedtimer.html")

    return app
