
from flask import Blueprint, request, jsonify, abort
from datetime import datetime, date as d, timedelta
from . import db
from .models import Event

api_bp = Blueprint("api", __name__)

def _parse_iso_date(s):
    try:
        return datetime.fromisoformat(s).date()
    except Exception:
        abort(400, description="Invalid date format")

@api_bp.get("/calendar")
def get_events():
    """Return events.
    Accepts any of:
      - ?month=YYYY-MM      (whole month)
      - ?date=YYYY-MM-DD    (single day)
      - ?from=YYYY-MM-DD&to=YYYY-MM-DD  (inclusive range; 'to' optional)
    Response: { ok: true, events: [...] }
    """
    month_str = request.args.get("month")
    date_str = request.args.get("date")
    from_str = request.args.get("from")
    to_str = request.args.get("to")

    q = Event.query

    if month_str:
        try:
            year, month = [int(x) for x in month_str.split("-")]
            start = d(year, month, 1)
            end = d(year + (1 if month == 12 else 0), (1 if month == 12 else month + 1), 1)
            q = q.filter(Event.date >= start, Event.date < end)
        except Exception:
            abort(400, description="Invalid month format, expected YYYY-MM")

    elif from_str or to_str:
        start = _parse_iso_date(from_str) if from_str else None
        end = _parse_iso_date(to_str) if to_str else None
        if start and end and end < start:
            abort(400, description="'to' must be >= 'from'")
        if start:
            q = q.filter(Event.date >= start)
        if end:
            # make 'to' inclusive by adding one day and using '<'
            q = q.filter(Event.date < (end + timedelta(days=1)))
    elif date_str:
        day = _parse_iso_date(date_str)
        q = q.filter_by(date=day)

    events = [e.to_dict() for e in q.order_by(Event.date.asc(), Event.id.asc()).all()]
    # Front-ends sometimes expect 'items' or 'events' keys; include both
    return jsonify({"ok": True, "events": events, "items": events})

@api_bp.post("/calendar")
def create_event():
    data = request.get_json(force=True, silent=True) or {}
    title = (data.get("title") or "").strip()
    date_str = data.get("date")
    etype = (data.get("type") or data.get("kind") or "note").strip()
    color = (data.get("color") or "").strip() or _default_color(etype)
    details = (data.get("details") or data.get("description") or "").strip()
    if not title or not date_str:
        abort(400, description="Missing title or date")
    day = _parse_iso_date(date_str)

    ev = Event(title=title, date=day, type=etype, color=color, details=details)
    db.session.add(ev)
    db.session.commit()
    return jsonify({"ok": True, "event": ev.to_dict()}), 201

@api_bp.patch("/calendar")
def update_event():
    """Update an existing event by JSON body containing id and any fields."""
    data = request.get_json(force=True, silent=True) or {}
    try:
        ev_id = int(data.get("id") or 0)
    except Exception:
        ev_id = 0
    if not ev_id:
        abort(400, description="Missing event id")

    ev = Event.query.get(ev_id)
    if not ev:
        abort(404, description="Event not found")

    # Apply updates if present
    if "title" in data:
        ev.title = (data.get("title") or "").strip() or ev.title
    new_date = data.get("date")
    if new_date:
        ev.date = _parse_iso_date(new_date)
    if "type" in data or "kind" in data:
        ev.type = (data.get("type") or data.get("kind") or ev.type).strip() or "note"
    if "color" in data:
        ev.color = (data.get("color") or "").strip() or ev.color
    if "details" in data or "description" in data:
        ev.details = (data.get("details") or data.get("description") or "").strip()

    db.session.commit()
    return jsonify({"ok": True, "event": ev.to_dict()})

@api_bp.delete("/calendar/<int:event_id>")
def delete_event(event_id):
    ev = Event.query.get_or_404(event_id)
    db.session.delete(ev)
    db.session.commit()
    return jsonify({"ok": True})

def _default_color(etype):
    return {"note": "#1976d2", "task": "#2e7d32", "job": "#ef6c00"}.get(etype, "#2e7d32")
