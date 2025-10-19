
from flask import Blueprint, request, jsonify, abort
from datetime import date, datetime
from . import db
from .models import Event

api_bp = Blueprint("api", __name__)

@api_bp.get("/calendar")
def get_events():
    # month=YYYY-MM or date=YYYY-MM-DD
    month_str = request.args.get("month")
    date_str = request.args.get("date")
    q = Event.query
    if month_str:
        try:
            year, month = [int(x) for x in month_str.split("-")]
            from datetime import date as d, timedelta
            start = d(year, month, 1)
            # compute end of month
            if month == 12:
                end = d(year+1, 1, 1)
            else:
                end = d(year, month+1, 1)
            q = q.filter(Event.date >= start, Event.date < end)
        except Exception:
            abort(400, description="Invalid month format, expected YYYY-MM")
    if date_str:
        try:
            day = datetime.fromisoformat(date_str).date()
            q = q.filter_by(date=day)
        except Exception:
            abort(400, description="Invalid date format")
    events = [e.to_dict() for e in q.order_by(Event.date.asc(), Event.id.asc()).all()]
    return jsonify({"ok": True, "events": events})

@api_bp.post("/calendar")
def create_event():
    data = request.get_json(force=True, silent=True) or {}
    title = (data.get("title") or "").strip()
    date_str = data.get("date")
    etype = (data.get("type") or "note").strip()
    color = (data.get("color") or "").strip() or default_color(etype)
    details = (data.get("details") or "").strip()
    if not title or not date_str:
        abort(400, description="Missing title or date")
    try:
        day = datetime.fromisoformat(date_str).date()
    except Exception:
        abort(400, description="Invalid date format")
    ev = Event(title=title, date=day, type=etype, color=color, details=details)
    db.session.add(ev)
    db.session.commit()
    return jsonify({"ok": True, "event": ev.to_dict()}), 201

def default_color(etype):
    return {"note": "#1976d2", "task": "#2e7d32", "job": "#ef6c00"}.get(etype, "#2e7d32")

@api_bp.delete("/calendar/<int:event_id>")
def delete_event(event_id):
    ev = Event.query.get_or_404(event_id)
    db.session.delete(ev)
    db.session.commit()
    return jsonify({"ok": True})
