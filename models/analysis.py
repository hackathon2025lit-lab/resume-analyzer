"""Analysis data-access helpers, including profile aggregate stats."""
from __future__ import annotations

import json
from typing import Optional

from models.db import get_db


def create(user_id: int, resume_id: int, job_role: str, criteria: dict,
           result: dict) -> int:
    db = get_db()
    overall = int(result.get("overall_score") or 0)
    ats = int(result.get("ats_score") or 0)
    cur = db.execute(
        """INSERT INTO analyses
             (user_id, resume_id, job_role, criteria_json, result_json,
              overall_score, ats_score)
           VALUES (?, ?, ?, ?, ?, ?, ?)""",
        (user_id, resume_id, job_role, json.dumps(criteria),
         json.dumps(result), overall, ats),
    )
    db.commit()
    return cur.lastrowid


def _row_to_dict(row) -> dict:
    data = dict(row)
    data["criteria"] = json.loads(data.get("criteria_json") or "{}")
    data["result"] = json.loads(data.get("result_json") or "{}")
    return data


def get(analysis_id: int, user_id: int) -> Optional[dict]:
    db = get_db()
    row = db.execute(
        """SELECT a.*, r.original_name AS resume_name
             FROM analyses a
             JOIN resumes r ON r.id = a.resume_id
            WHERE a.id = ? AND a.user_id = ?""",
        (analysis_id, user_id),
    ).fetchone()
    return _row_to_dict(row) if row else None


def list_for_user(user_id: int, search: str = "", sort: str = "newest") -> list:
    db = get_db()
    order = {
        "newest": "a.created_at DESC",
        "oldest": "a.created_at ASC",
        "score_high": "a.overall_score DESC",
        "score_low": "a.overall_score ASC",
        "ats_high": "a.ats_score DESC",
    }.get(sort, "a.created_at DESC")

    params: list = [user_id]
    where = "a.user_id = ?"
    if search:
        where += " AND (r.original_name LIKE ? OR a.job_role LIKE ?)"
        params.extend([f"%{search}%", f"%{search}%"])

    rows = db.execute(
        f"""SELECT a.*, r.original_name AS resume_name
              FROM analyses a
              JOIN resumes r ON r.id = a.resume_id
             WHERE {where}
             ORDER BY {order}""",
        params,
    ).fetchall()
    return [_row_to_dict(r) for r in rows]


def delete(analysis_id: int, user_id: int) -> bool:
    db = get_db()
    cur = db.execute(
        "DELETE FROM analyses WHERE id = ? AND user_id = ?",
        (analysis_id, user_id),
    )
    db.commit()
    return cur.rowcount > 0


def stats_for_user(user_id: int) -> dict:
    """Aggregate stats for the dashboard & profile. All default to 0."""
    db = get_db()
    row = db.execute(
        """SELECT
              COUNT(*)                         AS total,
              COALESCE(AVG(ats_score), 0)      AS avg_ats,
              COALESCE(AVG(overall_score), 0)  AS avg_overall,
              COALESCE(MAX(overall_score), 0)  AS best_overall
           FROM analyses WHERE user_id = ?""",
        (user_id,),
    ).fetchone()
    return {
        "total_analyses": int(row["total"] or 0),
        "avg_ats": round(float(row["avg_ats"] or 0)),
        "avg_overall": round(float(row["avg_overall"] or 0)),
        "best_overall": int(row["best_overall"] or 0),
    }
