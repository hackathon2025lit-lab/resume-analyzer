"""AI Resume Analyzer - Flask application entrypoint.

Run locally with:  python app.py
"""
from __future__ import annotations

from datetime import timedelta

from flask import Flask, render_template, session

from auth.routes import auth_bp, init_oauth
from config import Config
from models import db as db_module
from routes.dashboard import dashboard_bp
from routes.history import history_bp
from routes.profile import profile_bp
from routes.resume import resume_bp


def create_app() -> Flask:
    app = Flask(__name__, template_folder="templates", static_folder="static")

    app.config.from_object(Config)
    app.config["SECRET_KEY"] = Config.SECRET_KEY
    app.config["DATABASE_PATH"] = str(Config.DATABASE_PATH)
    app.config["MAX_CONTENT_LENGTH"] = Config.MAX_CONTENT_LENGTH
    app.config["PERMANENT_SESSION_LIFETIME"] = timedelta(days=7)
    app.config["SESSION_COOKIE_HTTPONLY"] = True
    app.config["SESSION_COOKIE_SAMESITE"] = "Lax"

    # Database + OAuth.
    db_module.register(app)
    init_oauth(app)

    # Blueprints.
    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(resume_bp)
    app.register_blueprint(history_bp)
    app.register_blueprint(profile_bp)

    _register_context(app)
    _register_errorhandlers(app)
    return app


def _register_context(app: Flask) -> None:
    @app.context_processor
    def inject_user():
        return {
            "current_user": {
                "id": session.get("user_id"),
                "name": session.get("user_name"),
                "email": session.get("user_email"),
                "picture": session.get("user_picture"),
            } if session.get("user_id") else None,
            "gemini_ready": Config.gemini_configured(),
        }


def _register_errorhandlers(app: Flask) -> None:
    @app.errorhandler(404)
    def not_found(_):
        return render_template("errors/404.html"), 404

    @app.errorhandler(413)
    def too_large(_):
        return render_template(
            "errors/error.html",
            code=413,
            message=f"File too large. Maximum size is "
                    f"{Config.MAX_CONTENT_LENGTH_MB} MB."), 413

    @app.errorhandler(500)
    def server_error(_):
        return render_template(
            "errors/error.html", code=500,
            message="Something went wrong. Please try again."), 500


app = create_app()


if __name__ == "__main__":
    app.run(host=Config.HOST, port=Config.PORT, debug=Config.DEBUG)
