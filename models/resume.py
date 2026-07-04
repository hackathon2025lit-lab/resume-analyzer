"""Resume data-access helpers."""
from __future__ import annotations

import json
from typing import Optional

from models.db import get_db


def create(user_id: int, filename: str, original_name: str, file_ext: str,
           file_size: int, raw_text: str, parsed: dict) -> int:
    db = get_db()
    cur = db.execute(
        """INSERT INTO resumes
             (user_id, filename, original_name, file_ext, file_size,
              raw_text, parsed_json)
           VALUES (?, ?, ?, ?, ?, ?, ?)""",
        (user_id, filename, original_name, file_ext, file_size,
         raw_text, json.dumps(parsed)),
    )
    db.commit()
    return cur.lastrowid


def get(resume_id: int, user_id: int) -> Optional[dict]:
    db = get_db()
    row = db.execute(
        "SELECT * FROM resumes WHERE id = ? AND user_id = ?",
        (resume_id, user_id),
    ).fetchone()
    if not row:
        return None
    data = dict(row)
    data["parsed"] = json.loads(data.get("parsed_json") or "{}")
    return data


def delete(resume_id: int, user_id: int) -> bool:
    db = get_db()
    cur = db.execute(
        "DELETE FROM resumes WHERE id = ? AND user_id = ?",
        (resume_id, user_id),
    )
    db.commit()
    return cur.rowcount > 0
