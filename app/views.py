
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

@ui_bp.route("/search")
def search():
    from .models import Event
    from . import db
    q = (request.args.get("q") or "").strip()
    results = []
    if q:
        like = f"%{q}%"
        # try to parse date
        date_eq = None
        try:
            if len(q) <= 10:
                from datetime import date as _d, datetime as _dt
                date_eq = _dt.fromisoformat(q).date()
        except Exception:
            date_eq = None
        # search events by title/details/date
        try:
            query = Event.query
            if date_eq:
                query = query.filter((Event.title.ilike(like)) | (Event.details.ilike(like)) | (Event.date == date_eq))
            else:
                query = query.filter((Event.title.ilike(like)) | (Event.details.ilike(like)))
            for ev in query.order_by(Event.date.desc()).limit(100).all():
                results.append({
                    "type": "Kalendář",
                    "title": ev.title,
                    "sub": (ev.details or "")[:160],
                    "date": ev.date.isoformat(),
                    "url": f"/calendar?month={ev.date.year}-{str(ev.date.month).zfill(2)}#d-{ev.date.isoformat()}",
                    "id": ev.id,
                })
        except Exception as e:
            # ignore db errors in search to avoid 500s
            pass
    return render_template("search.html", q=q, results=results)
