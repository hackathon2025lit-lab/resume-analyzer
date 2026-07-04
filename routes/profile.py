"""User profile blueprint."""
from __future__ import annotations

from flask import Blueprint, render_template, session

from models import analysis as analysis_model
from models import user as user_model
from utils.security import login_required

profile_bp = Blueprint("profile", __name__, url_prefix="/profile")


@profile_bp.route("/")
@login_required
def index():
    user_id = session["user_id"]
    user = user_model.get_by_id(user_id)
    stats = analysis_model.stats_for_user(user_id)
    recent = analysis_model.list_for_user(user_id)[:5]
    return render_template("profile.html", user=user, stats=stats,
                           recent=recent)
