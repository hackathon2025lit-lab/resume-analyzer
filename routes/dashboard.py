"""Dashboard blueprint."""
from __future__ import annotations

from flask import Blueprint, render_template, session

from models import analysis as analysis_model
from utils.constants import CRITERIA, JOB_ROLES
from utils.security import login_required

dashboard_bp = Blueprint("dashboard", __name__)


@dashboard_bp.route("/")
@login_required
def index():
    user_id = session["user_id"]
    stats = analysis_model.stats_for_user(user_id)
    recent = analysis_model.list_for_user(user_id)[:5]
    return render_template(
        "dashboard.html",
        stats=stats,
        recent=recent,
        job_roles=JOB_ROLES,
        criteria=CRITERIA,
    )
