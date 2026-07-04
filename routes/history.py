"""Analysis history: list, search, sort, view, delete, download, export."""
from __future__ import annotations

import io
import json
from datetime import datetime

from flask import (Blueprint, jsonify, render_template, request, send_file,
                   session)

from models import analysis as analysis_model
from services import report_service
from utils.security import login_required

history_bp = Blueprint("history", __name__, url_prefix="/history")


@history_bp.route("/")
@login_required
def index():
    search = request.args.get("q", "").strip()
    sort = request.args.get("sort", "newest")
    items = analysis_model.list_for_user(session["user_id"], search, sort)
    return render_template("history.html", items=items, search=search,
                           sort=sort)


@history_bp.route("/<int:analysis_id>", methods=["DELETE"])
@login_required
def delete(analysis_id: int):
    ok = analysis_model.delete(analysis_id, session["user_id"])
    return jsonify(ok=ok)


@history_bp.route("/<int:analysis_id>/download/<fmt>")
@login_required
def download(analysis_id: int, fmt: str):
    record = analysis_model.get(analysis_id, session["user_id"])
    if not record:
        return jsonify(ok=False, error="Not found."), 404

    stamp = datetime.utcnow().strftime("%Y%m%d")
    safe = "".join(c for c in (record.get("resume_name") or "resume")
                   if c.isalnum() or c in "-_")[:40] or "resume"

    if fmt == "pdf":
        data = report_service.build_pdf(record)
        return send_file(io.BytesIO(data), mimetype="application/pdf",
                         as_attachment=True,
                         download_name=f"analysis_{safe}_{stamp}.pdf")
    if fmt == "txt":
        data = report_service.build_txt(record)
        return send_file(io.BytesIO(data), mimetype="text/plain",
                         as_attachment=True,
                         download_name=f"analysis_{safe}_{stamp}.txt")
    return jsonify(ok=False, error="Unsupported format."), 400


@history_bp.route("/export")
@login_required
def export():
    """Export the full history as a JSON file."""
    items = analysis_model.list_for_user(session["user_id"])
    payload = json.dumps({
        "exported_at": datetime.utcnow().isoformat(),
        "count": len(items),
        "analyses": [
            {
                "id": it["id"],
                "resume_name": it.get("resume_name"),
                "job_role": it.get("job_role"),
                "overall_score": it.get("overall_score"),
                "ats_score": it.get("ats_score"),
                "created_at": it.get("created_at"),
                "result": it.get("result"),
            }
            for it in items
        ],
    }, indent=2)
    return send_file(
        io.BytesIO(payload.encode("utf-8")),
        mimetype="application/json", as_attachment=True,
        download_name="resume_analysis_history.json")
