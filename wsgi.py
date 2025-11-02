from flask import Flask, render_template
from gd.api import register_api

app = Flask(__name__)
register_api(app)

@app.get('/')
def index():
    return render_template('calendar.html', title='Kalendář', active='calendar')

@app.get('/calendar')
def calendar_page():
    return render_template('calendar.html', title='Kalendář', active='calendar')

@app.get('/timesheets')
def timesheets_page():
    return render_template('timesheets.html', title='Výkazy hodin', active='timesheets')

@app.get('/employees')
def employees_page():
    return render_template('employees.html', title='Zaměstnanci', active='employees')

@app.get('/jobs')
def jobs_page():
    return render_template('jobs.html', title='Zakázky', active='jobs')

@app.get('/tasks')
def tasks_page():
    return render_template('tasks.html', title='Úkoly', active='tasks')

@app.get('/warehouse')
def warehouse_page():
    return render_template('warehouse.html', title='Sklad', active='warehouse')

@app.get('/users')
def users_page():
    return render_template('users.html', title='Uživatelé', active='users')