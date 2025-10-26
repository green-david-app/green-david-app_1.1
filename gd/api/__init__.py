
from flask import Blueprint, jsonify, request
from ..db import db_session
from ..models import Employee, Job, Task, CalendarEvent, Timesheet
from datetime import datetime, date

api_bp = Blueprint('api', __name__)

def to_dict(obj):
    if isinstance(obj, Employee):
        return {"id": obj.id, "name": obj.name, "email": obj.email}
    if isinstance(obj, Job):
        return {"id": obj.id, "title": obj.title, "client": obj.client}
    if isinstance(obj, Task):
        return {"id": obj.id, "job_id": obj.job_id, "name": obj.name, "notes": obj.notes}
    if isinstance(obj, CalendarEvent):
        return {"id": obj.id, "date": obj.date.isoformat(), "title": obj.title, "note": obj.note, "job_id": obj.job_id, "task_id": obj.task_id}
    if isinstance(obj, Timesheet):
        return {"id": obj.id, "employee_id": obj.employee_id, "date": obj.date.isoformat(), "hours": obj.hours, "job_id": obj.job_id, "task_id": obj.task_id, "note": obj.note}
    return {}

# Helper to parse date
def parse_date(s):
    return datetime.strptime(s, "%Y-%m-%d").date()

# Generic simple CRUD endpoints (minimal validation)
@api_bp.route('/employees', methods=['GET', 'POST'])
def employees():
    if request.method == 'POST':
        data = request.get_json(force=True)
        e = Employee(name=data['name'], email=data.get('email'))
        db_session.add(e); db_session.commit()
        return jsonify(to_dict(e)), 201
    all_e = db_session.query(Employee).all()
    return jsonify([to_dict(e) for e in all_e])

@api_bp.route('/jobs', methods=['GET', 'POST'])
def jobs():
    if request.method == 'POST':
        data = request.get_json(force=True)
        j = Job(title=data['title'], client=data.get('client'))
        db_session.add(j); db_session.commit()
        return jsonify(to_dict(j)), 201
    all_j = db_session.query(Job).all()
    return jsonify([to_dict(j) for j in all_j])

@api_bp.route('/tasks', methods=['GET', 'POST'])
def tasks():
    if request.method == 'POST':
        data = request.get_json(force=True)
        t = Task(job_id=data['job_id'], name=data['name'], notes=data.get('notes'))
        db_session.add(t); db_session.commit()
        return jsonify(to_dict(t)), 201
    all_t = db_session.query(Task).all()
    return jsonify([to_dict(t) for t in all_t])

@api_bp.route('/calendar', methods=['GET', 'POST'])
def calendar_events():
    if request.method == 'POST':
        data = request.get_json(force=True)
        ce = CalendarEvent(date=parse_date(data['date']), title=data['title'], note=data.get('note'), job_id=data.get('job_id'), task_id=data.get('task_id'))
        db_session.add(ce); db_session.commit()
        return jsonify(to_dict(ce)), 201
    # optional ?month=YYYY-MM
    month = request.args.get('month')
    q = db_session.query(CalendarEvent)
    if month:
        y, m = map(int, month.split('-'))
        from calendar import monthrange
        start = date(y, m, 1)
        end = date(y, m, monthrange(y, m)[1])
        q = q.filter(CalendarEvent.date >= start, CalendarEvent.date <= end)
    items = q.order_by(CalendarEvent.date.asc()).all()
    return jsonify([to_dict(i) for i in items])

@api_bp.route('/timesheets', methods=['GET', 'POST'])
def timesheets():
    if request.method == 'POST':
        data = request.get_json(force=True)
        ts = Timesheet(employee_id=data['employee_id'], date=parse_date(data['date']), hours=float(data['hours']), job_id=data.get('job_id'), task_id=data.get('task_id'), note=data.get('note'))
        db_session.add(ts); db_session.commit()
        return jsonify(to_dict(ts)), 201
    # optional filters: employee_id, from, to
    q = db_session.query(Timesheet)
    emp = request.args.get('employee_id')
    if emp:
        q = q.filter(Timesheet.employee_id == int(emp))
    frm = request.args.get('from')
    to = request.args.get('to')
    if frm:
        q = q.filter(Timesheet.date >= parse_date(frm))
    if to:
        q = q.filter(Timesheet.date <= parse_date(to))
    items = q.order_by(Timesheet.date.desc()).all()
    return jsonify([to_dict(i) for i in items])
