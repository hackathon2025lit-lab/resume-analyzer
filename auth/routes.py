"""Authentication blueprint: Google Sign-In (OAuth 2.0 / OpenID Connect).

Google credentials are read from the environment (GOOGLE_CLIENT_ID /
GOOGLE_CLIENT_SECRET). When they are not configured the login page shows a
clear notice instead of failing silently.

An optional, off-by-default developer login (ALLOW_DEV_LOGIN=1) exists purely
to let the app be exercised locally without external credentials. It creates
a REAL user row (no demo/sample data) and is never enabled by default.
"""
from __future__ import annotations

import os

from authlib.integrations.flask_client import OAuth
from flask import (Blueprint, current_app, flash, redirect, render_template,
                   session, url_for)

from config import Config
from models import user as user_model

auth_bp = Blueprint("auth", __name__, url_prefix="/auth")

oauth = OAuth()
_google = None


def init_oauth(app) -> None:
    """Register the Google OAuth client if credentials are present."""
    global _google
    oauth.init_app(app)
    if Config.google_oauth_configured():
        _google = oauth.register(
            name="google",
            client_id=Config.GOOGLE_CLIENT_ID,
            client_secret=Config.GOOGLE_CLIENT_SECRET,
            server_metadata_url=Config.GOOGLE_DISCOVERY_URL,
            client_kwargs={"scope": "openid email profile"},
        )


@auth_bp.route("/login")
def login():
    if session.get("user_id"):
        return redirect(url_for("dashboard.index"))
    return render_template(
        "login.html",
        oauth_configured=Config.google_oauth_configured(),
        dev_login=_as_bool(os.getenv("ALLOW_DEV_LOGIN")),
    )


@auth_bp.route("/google")
def google_login():
    if not Config.google_oauth_configured() or _google is None:
        flash("Google OAuth is not configured. Set GOOGLE_CLIENT_ID and "
              "GOOGLE_CLIENT_SECRET in your .env file.", "error")
        return redirect(url_for("auth.login"))
    redirect_uri = url_for("auth.callback", _external=True)
    return _google.authorize_redirect(redirect_uri)


@auth_bp.route("/callback")
def callback():
    if _google is None:
        flash("Google OAuth is not configured.", "error")
        return redirect(url_for("auth.login"))
    try:
        token = _google.authorize_access_token()
        info = token.get("userinfo") or _google.parse_id_token(token)
    except Exception as exc:  # pragma: no cover - network dependent
        current_app.logger.warning("OAuth callback failed: %s", exc)
        flash("Google login failed. Please try again.", "error")
        return redirect(url_for("auth.login"))

    if not info or not info.get("email"):
        flash("Could not read your Google profile. Please try again.",
              "error")
        return redirect(url_for("auth.login"))

    record = user_model.upsert_from_google(
        google_id=info.get("sub"),
        email=info.get("email"),
        name=info.get("name") or info.get("email").split("@")[0],
        picture=info.get("picture"),
    )
    _establish_session(record)
    flash(f"Welcome, {record['name']}!", "success")
    return redirect(url_for("dashboard.index"))


@auth_bp.route("/dev-login")
def dev_login():
    """Local-only convenience login (guarded by ALLOW_DEV_LOGIN)."""
    if not _as_bool(os.getenv("ALLOW_DEV_LOGIN")):
        flash("Developer login is disabled.", "error")
        return redirect(url_for("auth.login"))
    record = user_model.upsert_from_google(
        google_id="dev-local-user",
        email="dev@localhost",
        name="Local Developer",
        picture=None,
    )
    _establish_session(record)
    flash("Signed in with the local developer account.", "success")
    return redirect(url_for("dashboard.index"))


@auth_bp.route("/logout")
def logout():
    session.clear()
    flash("You have been logged out.", "success")
    return redirect(url_for("auth.login"))


def _establish_session(record: dict) -> None:
    session.clear()
    session["user_id"] = record["id"]
    session["user_name"] = record["name"]
    session["user_email"] = record["email"]
    session["user_picture"] = record.get("picture")
    session.permanent = True


def _as_bool(value: str | None) -> bool:
    return bool(value) and value.strip().lower() in {"1", "true", "yes", "on"}
