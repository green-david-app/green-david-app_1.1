
from flask import Blueprint, render_template, request, redirect, url_for, Response
from datetime import date
from ..db import db_session
from ..models import Employee, Timesheet

bp = Blueprint('timesheets', __name__)

@bp.route('/timesheets')
def timesheets_page():
    employees = db_session.query(Employee).all()
    emp_id = request.args.get('employee_id', type=int)
    q = db_session.query(Timesheet)
    if emp_id:
        q = q.filter(Timesheet.employee_id == emp_id)
    times = q.order_by(Timesheet.date.desc()).all()
    return render_template('timesheets.html', employees=employees, times=times, emp_id=emp_id)

@bp.route('/timesheets/add', methods=['POST'])
def add_timesheet():
    emp_id = int(request.form['employee_id'])
    d = date.fromisoformat(request.form['date'])
    hours = float(request.form['hours'])
    note = request.form.get('note')
    ts = Timesheet(employee_id=emp_id, date=d, hours=hours, note=note)
    db_session.add(ts)
    db_session.commit()
    return redirect(url_for('timesheets.timesheets_page'))

@bp.route('/timesheets/export.csv')
def export_csv():
    # Optional filter by employee_id
    emp_id = request.args.get('employee_id', type=int)
    q = db_session.query(Timesheet)
    if emp_id:
        q = q.filter(Timesheet.employee_id == emp_id)
    times = q.order_by(Timesheet.date.asc()).all()
    # Prepare CSV
    lines = ["id;employee_id;date;hours;job_id;task_id;note"]
    for t in times:
        lines.append(f"{t.id};{t.employee_id};{t.date.isoformat()};{t.hours};{t.job_id or ''};{t.task_id or ''};{(t.note or '').replace(';', ',')}")
    csv_data = "\n".join(lines)
    return Response(csv_data, mimetype='text/csv',
                    headers={'Content-Disposition': 'attachment; filename="timesheets.csv"'})
