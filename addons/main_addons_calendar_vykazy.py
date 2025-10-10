
from flask import Blueprint, render_template

# Použijeme unikátní jméno blueprintu, aby nenarážel na dřívější registrace
bp = Blueprint("gd_addons_calendar_vykazy", __name__)

@bp.get("/calendar")
def calendar_page():
    return render_template("calendar.html")

@bp.get("/vykazy")
def worklogs_page():
    return render_template("worklogs.html")
