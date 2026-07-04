"""Security helpers: filename sanitization, extension validation, decorators."""
from __future__ import annotations

import functools
import uuid
from pathlib import Path

from flask import flash, redirect, session, url_for
from werkzeug.utils import secure_filename

from config import Config


def allowed_file(filename: str) -> bool:
    return "." in filename and \
        filename.rsplit(".", 1)[1].lower() in Config.ALLOWED_EXTENSIONS


def file_extension(filename: str) -> str:
    return filename.rsplit(".", 1)[1].lower() if "." in filename else ""


def safe_stored_name(original_name: str) -> str:
    """Return a collision-free, sanitized storage filename."""
    cleaned = secure_filename(original_name) or "resume"
    ext = file_extension(cleaned) or "dat"
    stem = cleaned.rsplit(".", 1)[0] if "." in cleaned else cleaned
    return f"{stem}_{uuid.uuid4().hex[:12]}.{ext}"


def login_required(view):
    """Redirect anonymous users to the login page."""
    @functools.wraps(view)
    def wrapped(*args, **kwargs):
        if not session.get("user_id"):
            flash("Please sign in to continue.", "error")
            return redirect(url_for("auth.login"))
        return view(*args, **kwargs)
    return wrapped


def within_upload_dir(path: Path) -> bool:
    """Guard against path traversal for files we intend to serve/delete."""
    try:
        path.resolve().relative_to(Config.UPLOAD_DIR.resolve())
        return True
    except ValueError:
        return False
