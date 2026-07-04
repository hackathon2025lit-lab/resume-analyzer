"""SQLite connection management and schema initialization.

Uses Flask's application context so each request gets a single shared
connection that is closed automatically when the request ends.
"""
import sqlite3
from pathlib import Path

from flask import current_app, g

from config import Config


def get_db() -> sqlite3.Connection:
    """Return a request-scoped SQLite connection."""
    if "db" not in g:
        conn = sqlite3.connect(
            current_app.config["DATABASE_PATH"],
            detect_types=sqlite3.PARSE_DECLTYPES,
        )
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON;")
        g.db = conn
    return g.db


def close_db(exception=None) -> None:
    """Close the request-scoped connection (registered as teardown)."""
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db(app) -> None:
    """Create tables from schema.sql if they do not yet exist."""
    schema_path = Path(Config.BASE_DIR) / "database" / "schema.sql"
    with app.app_context():
        db = sqlite3.connect(app.config["DATABASE_PATH"])
        with open(schema_path, "r", encoding="utf-8") as fh:
            db.executescript(fh.read())
        db.commit()
        db.close()


def register(app) -> None:
    """Wire up teardown handler and ensure the schema exists."""
    Config.ensure_dirs()
    app.teardown_appcontext(close_db)
    init_db(app)
