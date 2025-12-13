from flask import Flask, render_template
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
    CORS(app)

    # Init Firebase / MQTT / Scheduler
    init_extensions(app)

    # Blueprints
    app.register_blueprint(telemetry_bp, url_prefix="/telemetry")
    app.register_blueprint(control_bp, url_prefix="/control")
    app.register_blueprint(admin_bp, url_prefix="/admin")
    app.register_blueprint(dashboard_bp, url_prefix="/dashboard")
    app.register_blueprint(chatbot_bp, url_prefix="/chatbot")

    # Web routes
    @app.route("/")
    def home():
        return render_template("index.html")

    @app.route("/admin-page")
    def admin_page():
        return render_template("admin.html")

    @app.route("/temperature")
    def temperature_page():
        return render_template("temperature.html")

    @app.route("/turbidity")
    def turbidity_page():
        return render_template("turbidity.html")

    @app.route("/feedtimer")
    def feed_timer_page():
        return render_template("feedtimer.html")

    return app
