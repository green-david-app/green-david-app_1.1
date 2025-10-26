
from flask import Blueprint, render_template, request, redirect, url_for
from datetime import date, timedelta
from calendar import monthrange
from ..db import db_session
from ..models import CalendarEvent

bp = Blueprint('calendar', __name__)

@bp.route('/calendar')
def calendar_page():
    today = date.today()
    y = int(request.args.get('y', today.year))
    m = int(request.args.get('m', today.month))

    first_weekday, days_in_month = monthrange(y, m)
    grid_start = date(y, m, 1) - timedelta(days=(first_weekday if first_weekday != 6 else 0))
    grid = [grid_start + timedelta(days=i) for i in range(6*7)]

    events = db_session.query(CalendarEvent).filter(CalendarEvent.date >= grid[0], CalendarEvent.date <= grid[-1]).all()
    events_by_day = {}
    for e in events:
        events_by_day.setdefault(e.date, []).append(e)

    prev_m = m - 1 or 12
    prev_y = y - 1 if m == 1 else y
    next_m = m + 1 if m < 12 else 1
    next_y = y + 1 if m == 12 else y

    return render_template('calendar.html', y=y, m=m, grid=grid, today=today, events_by_day=events_by_day,
                           prev_y=prev_y, prev_m=prev_m, next_y=next_y, next_m=next_m)

@bp.route('/calendar/add', methods=['POST'])
def add_event():
    from flask import request
    d = request.form.get('date')
    title = request.form.get('title')
    note = request.form.get('note')
    if d and title:
        ce = CalendarEvent(date=date.fromisoformat(d), title=title, note=note)
        from ..db import db_session
        db_session.add(ce)
        db_session.commit()
    return redirect(url_for('calendar.calendar_page'))
