# app/views_redirect.py — redirect legacy paths to Flask views
from flask import Blueprint, redirect, url_for

redirects_bp = Blueprint("redirects", __name__)

@redirects_bp.route("/calendar.html")
def _redir_calendar_html():
    return redirect(url_for("ui.calendar"), code=301)
