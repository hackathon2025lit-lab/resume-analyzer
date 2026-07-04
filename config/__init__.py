"""Application configuration loaded from environment variables.

All secrets (Google OAuth credentials, Gemini API key, Flask secret key)
are read from the environment / .env file and are never hard-coded.
"""
import os
from pathlib import Path

from dotenv import load_dotenv

# Project root = parent of the `config` package directory.
BASE_DIR = Path(__file__).resolve().parent.parent

# Load variables from a local .env file if present.
load_dotenv(BASE_DIR / ".env")


def _as_bool(value: str | None, default: bool = False) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


class Config:
    """Central configuration object."""

    BASE_DIR = BASE_DIR

    # Flask
    SECRET_KEY = os.getenv("FLASK_SECRET_KEY", "dev-insecure-secret-change-me")
    DEBUG = _as_bool(os.getenv("FLASK_DEBUG"), default=False)
    ENV = os.getenv("FLASK_ENV", "production")

    # Server
    HOST = os.getenv("HOST", "127.0.0.1")
    PORT = int(os.getenv("PORT", "5000"))

    # Google OAuth
    GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID", "")
    GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET", "")
    GOOGLE_DISCOVERY_URL = (
        "https://accounts.google.com/.well-known/openid-configuration"
    )

    # Gemini
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
    GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")

    # Uploads
    MAX_CONTENT_LENGTH_MB = int(os.getenv("MAX_CONTENT_LENGTH_MB", "10"))
    MAX_CONTENT_LENGTH = MAX_CONTENT_LENGTH_MB * 1024 * 1024
    UPLOAD_DIR = BASE_DIR / "uploads"
    REPORT_DIR = BASE_DIR / "reports"
    ALLOWED_EXTENSIONS = {"pdf", "docx"}

    # Database
    DATABASE_PATH = BASE_DIR / os.getenv("DATABASE_PATH", "database/app.db")

    @classmethod
    def google_oauth_configured(cls) -> bool:
        return bool(cls.GOOGLE_CLIENT_ID and cls.GOOGLE_CLIENT_SECRET)

    @classmethod
    def gemini_configured(cls) -> bool:
        return bool(cls.GEMINI_API_KEY)

    @classmethod
    def ensure_dirs(cls) -> None:
        cls.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
        cls.REPORT_DIR.mkdir(parents=True, exist_ok=True)
        cls.DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)
