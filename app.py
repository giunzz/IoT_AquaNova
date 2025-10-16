from flask import Flask, render_template
from flask_cors import CORS
from config import Config
from firebase_admin_init import init_firebase
from blueprints.telemetry.routes import telemetry_bp
from blueprints.control.routes import control_bp
from blueprints.control.scheduler import start_scheduler   # 🆕 thêm dòng này
from blueprints.admin.routes import admin_bp
from blueprints.dashboard.routes import dashboard_bp
from mqtt.listener import start_mqtt_background


def create_app():
    app = Flask(__name__, static_folder="static", template_folder="templates")
    app.config.from_object(Config)
    CORS(app)

    # Firebase
    init_firebase()

    # Blueprints
    app.register_blueprint(telemetry_bp, url_prefix="/telemetry")
    app.register_blueprint(control_bp, url_prefix="/control")
    app.register_blueprint(admin_bp, url_prefix="/admin")
    app.register_blueprint(dashboard_bp, url_prefix="/dashboard")
    # Trang web
    @app.get("/")
    def home():
        return render_template("index.html")

    @app.get("/admin")
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

    # Bắt đầu MQTT listener và scheduler
    start_mqtt_background(app)
    with app.app_context():
        start_scheduler()  

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(debug=True)
