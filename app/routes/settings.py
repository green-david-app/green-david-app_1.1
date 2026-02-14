# Green David App
from flask import Blueprint, jsonify, request, send_from_directory
from app.database import get_db
from app.utils.permissions import require_auth, requires_role

settings_bp = Blueprint('settings', __name__)


@settings_bp.route("/settings.html")
def settings_html():
    return send_from_directory(".", "settings.html")


# Settings routes from main.py
@settings_bp.route("/settings.html")
def page_settings():
    return send_from_directory(".", "settings.html")

@settings_bp.route("/reports.html")
def page_reports():
    return send_from_directory(".", "reports.html")

# ----------------- Job detail UI routes -----------------
