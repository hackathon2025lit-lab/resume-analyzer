"""User data-access helpers."""
from __future__ import annotations

from typing import Optional

from models.db import get_db


def upsert_from_google(google_id: str, email: str, name: str,
                       picture: str | None) -> dict:
    """Create the user on first login, otherwise update last_login_at."""
    db = get_db()
    existing = db.execute(
        "SELECT * FROM users WHERE google_id = ?", (google_id,)
    ).fetchone()

    if existing is None:
        cur = db.execute(
            """INSERT INTO users (google_id, email, name, picture)
               VALUES (?, ?, ?, ?)""",
            (google_id, email, name, picture),
        )
        db.commit()
        user_id = cur.lastrowid
    else:
        db.execute(
            """UPDATE users
                  SET name = ?, picture = ?, last_login_at = datetime('now')
                WHERE google_id = ?""",
            (name, picture, google_id),
        )
        db.commit()
        user_id = existing["id"]

    return get_by_id(user_id)


def get_by_id(user_id: int) -> Optional[dict]:
    db = get_db()
    row = db.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    return dict(row) if row else None
