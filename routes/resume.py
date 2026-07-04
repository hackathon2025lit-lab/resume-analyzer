"""Resume upload, parsing and AI analysis blueprint (JSON API + views)."""
from __future__ import annotations

import json

from flask import (Blueprint, jsonify, render_template, request, session,
                   url_for)

from config import Config
from models import analysis as analysis_model
from models import resume as resume_model
from services import ai_service, parser_service
from utils.constants import CRITERIA, JOB_ROLES
from utils.security import (allowed_file, file_extension, login_required,
                            safe_stored_name, within_upload_dir)

resume_bp = Blueprint("resume", __name__, url_prefix="/resume")


@resume_bp.route("/upload", methods=["POST"])
@login_required
def upload():
    """Accept a PDF/DOCX, validate, store, parse and return JSON."""
    if "resume" not in request.files:
        return jsonify(ok=False, error="No file part in the request."), 400

    file = request.files["resume"]
    if not file or file.filename == "":
        return jsonify(ok=False, error="No file selected."), 400

    if not allowed_file(file.filename):
        return jsonify(
            ok=False,
            error="Invalid file type. Only PDF, DOCX and ZIP are allowed."), 400

    # Size check (Flask MAX_CONTENT_LENGTH also enforces the hard limit).
    file.seek(0, 2)
    size = file.tell()
    file.seek(0)
    if size == 0:
        return jsonify(ok=False, error="The file is empty."), 400
    if size > Config.MAX_CONTENT_LENGTH:
        return jsonify(
            ok=False,
            error=f"File too large. Maximum size is "
                  f"{Config.MAX_CONTENT_LENGTH_MB} MB."), 413

    ext = file_extension(file.filename)
    stored_name = safe_stored_name(file.filename)
    dest = Config.UPLOAD_DIR / stored_name
    if not within_upload_dir(dest):
        return jsonify(ok=False, error="Invalid file path."), 400

    file.save(str(dest))

    try:
        raw_text, parsed = parser_service.parse_resume(dest, ext)
    except Exception as exc:
        dest.unlink(missing_ok=True)
        return jsonify(
            ok=False,
            error=f"Could not read the resume: {exc}"), 422

    resume_id = resume_model.create(
        user_id=session["user_id"], filename=stored_name,
        original_name=file.filename, file_ext=ext, file_size=size,
        raw_text=raw_text, parsed=parsed,
    )

    return jsonify(
        ok=True,
        resume_id=resume_id,
        filename=file.filename,
        size=size,
        parsed=parsed,
    )


@resume_bp.route("/<int:resume_id>", methods=["DELETE"])
@login_required
def remove(resume_id: int):
    """Delete an uploaded resume (and its file) before/after analysis."""
    record = resume_model.get(resume_id, session["user_id"])
    if not record:
        return jsonify(ok=False, error="Resume not found."), 404
    path = Config.UPLOAD_DIR / record["filename"]
    if within_upload_dir(path):
        path.unlink(missing_ok=True)
    resume_model.delete(resume_id, session["user_id"])
    return jsonify(ok=True)


@resume_bp.route("/analyze", methods=["POST"])
@login_required
def analyze():
    """Run the AI analysis for an uploaded resume."""
    data = request.get_json(silent=True) or {}
    resume_id = data.get("resume_id")
    role = (data.get("job_role") or "").strip()
    custom_role = (data.get("custom_role") or "").strip()
    criteria = data.get("criteria") or {}
    delete_after = bool(data.get("delete_after"))

    if role == "Custom Role" and custom_role:
        role = custom_role
    if not role:
        role = "Software Engineer"

    if not resume_id:
        return jsonify(ok=False, error="No resume selected."), 400

    record = resume_model.get(int(resume_id), session["user_id"])
    if not record:
        return jsonify(ok=False, error="Resume not found."), 404

    # Normalize criteria weights to integers.
    clean_criteria = {}
    for key, value in criteria.items():
        try:
            clean_criteria[key] = int(float(value))
        except (TypeError, ValueError):
            continue

    try:
        result = ai_service.analyze(
            raw_text=record["raw_text"],
            parsed=record["parsed"],
            role=role,
            criteria=clean_criteria,
        )
    except Exception as exc:
        return jsonify(ok=False, error=f"Analysis failed: {exc}"), 500

    analysis_id = analysis_model.create(
        user_id=session["user_id"], resume_id=int(resume_id),
        job_role=role, criteria=clean_criteria, result=result,
    )

    if delete_after:
        path = Config.UPLOAD_DIR / record["filename"]
        if within_upload_dir(path):
            path.unlink(missing_ok=True)

    return jsonify(ok=True, analysis_id=analysis_id, result=result,
                   redirect=url_for("resume.view_analysis",
                                    analysis_id=analysis_id))


@resume_bp.route("/analysis/<int:analysis_id>")
@login_required
def view_analysis(analysis_id: int):
    record = analysis_model.get(analysis_id, session["user_id"])
    if not record:
        return render_template("errors/404.html"), 404
    return render_template(
        "analysis.html",
        analysis=record,
        result=record["result"],
        result_json=json.dumps(record["result"]),
        job_roles=JOB_ROLES,
        criteria=CRITERIA,
    )
