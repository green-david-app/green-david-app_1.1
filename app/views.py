
from flask import Blueprint, render_template, request
from datetime import date, datetime

ui_bp = Blueprint("ui", __name__)

@ui_bp.route("/")
def index():
    return render_template("calendar.html")

@ui_bp.route("/calendar")
def calendar():
    # month param optional
    month = request.args.get("month")
    return render_template("calendar.html", month=month)


@ui_bp.route("/calendar.html")
def calendar_html():
    # Force using Flask template (not any stale static file)
    month = request.args.get("month")
    return render_template("calendar.html", month=month)
