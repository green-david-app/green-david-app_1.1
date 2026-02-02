"""
Planning Module API - WORKING VERSION
Uses EXISTING data from jobs, tasks, timesheets, employees
"""
from flask import jsonify, request, session
from datetime import datetime, date, timedelta
import os

# Optional requests for weather
try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False

get_db = None
WEATHER_API_KEY = os.environ.get("OPENWEATHER_API_KEY", "")
WEATHER_API_URL = "https://api.openweathermap.org/data/2.5/forecast"

def get_weather_forecast(lat=49.7384, lon=14.1547):
    """Get weather with fallback to mock data"""
    if not REQUESTS_AVAILABLE or not WEATHER_API_KEY:
        return {
            'temp': 8, 'feels_like': 6, 'description': 'Zataženo',
            'icon': '04d', 'humidity': 75, 'wind_speed': 3.5,
            'rain_probability': 20, 'suitable_for_outdoor': True,
            'forecast_3h': []
        }
    
    try:
        response = requests.get(WEATHER_API_URL, params={
            'lat': lat, 'lon': lon, 'appid': WEATHER_API_KEY,
            'units': 'metric', 'lang': 'cz', 'cnt': 8
        }, timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            current = data['list'][0]
            rain_prob = current.get('pop', 0) * 100
            temp = current['main']['temp']
            weather_main = current['weather'][0]['main'].lower()
            suitable = not (rain_prob > 60 or temp < 0 or temp > 35 or weather_main in ['thunderstorm', 'snow', 'extreme'])
            
            return {
                'temp': round(temp, 1), 'feels_like': round(current['main']['feels_like'], 1),
                'description': current['weather'][0]['description'].capitalize(),
                'icon': current['weather'][0]['icon'], 'humidity': current['main']['humidity'],
                'wind_speed': round(current['wind']['speed'], 1), 'rain_probability': round(rain_prob),
                'suitable_for_outdoor': suitable,
                'forecast_3h': [{'time': item['dt_txt'], 'temp': round(item['main']['temp'], 1),
                                'description': item['weather'][0]['description'],
                                'rain_prob': round(item.get('pop', 0) * 100)} for item in data['list'][:8]]
            }
    except:
        pass
    
    return {'temp': 10, 'description': 'Počasí nedostupné', 'suitable_for_outdoor': True, 'forecast_3h': []}

# ================================================================
# TIMELINE
# ================================================================
def get_planning_timeline():
    try:
        status = request.args.get('status')
        db = get_db()
        
        query = """SELECT j.id, j.name, j.code, j.status, j.start_date, j.planned_end_date,
                   j.deadline, j.progress, j.priority, j.estimated_hours, j.actual_hours,
                   j.estimated_value as budget_total, j.actual_value, j.completed_at
                   FROM jobs j WHERE j.status != 'cancelled'"""
        params = []
        if status:
            query += " AND j.status = ?"
            params.append(status)
        query += " ORDER BY CASE WHEN j.priority IS NULL THEN 1 ELSE 0 END, j.priority, j.deadline"
        
        projects = db.execute(query, params).fetchall()
        result = []
        for proj in projects:
            task_stats = db.execute("""SELECT COUNT(*) as task_count,
                COUNT(CASE WHEN t.status = 'done' THEN 1 END) as completed_tasks
                FROM tasks t WHERE t.job_id = ?""", (proj['id'],)).fetchone()
            
            tasks = db.execute("""SELECT t.id, t.title, t.status, t.due_date, t.employee_id
                FROM tasks t WHERE t.job_id = ? ORDER BY t.due_date ASC""", (proj['id'],)).fetchall()
            
            proj_dict = dict(proj)
            proj_dict['task_count'] = task_stats['task_count']
            proj_dict['completed_tasks'] = task_stats['completed_tasks']
            result.append({'project': proj_dict, 'tasks': [dict(t) for t in tasks],
                          'task_count': task_stats['task_count'],
                          'completed_tasks': task_stats['completed_tasks']})
        
        return jsonify({'success': True, 'timeline': result})
    except Exception as e:
        print(f"[ERROR] Timeline: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500

# ================================================================
# DAILY
# ================================================================
def get_planning_daily(target_date=None):
    try:
        if not target_date:
            target_date = request.args.get('date', date.today().isoformat())
        db = get_db()
        
        tasks = db.execute("""SELECT t.id, t.title, t.status, t.due_date, t.description,
            j.id as job_id, j.name as job_name, j.code as job_code, e.name as assigned_employee
            FROM tasks t LEFT JOIN jobs j ON t.job_id = j.id LEFT JOIN employees e ON t.employee_id = e.id
            WHERE t.due_date = ? ORDER BY t.status, t.id""", (target_date,)).fetchall()
        
        timesheets_today = db.execute("""SELECT ts.id, e.id as employee_id, e.name as employee_name,
            e.role, j.id as job_id, j.name as job_name, j.code as job_code, ts.hours, ts.date, ts.note
            FROM timesheets ts LEFT JOIN employees e ON ts.employee_id = e.id
            LEFT JOIN jobs j ON ts.job_id = j.id WHERE ts.date = ? ORDER BY e.name""",
            (target_date,)).fetchall()
        
        active_jobs = db.execute("""SELECT j.id, j.name, j.code, j.status, j.start_date, j.deadline, j.progress
            FROM jobs j WHERE j.status IN ('Plán', 'Probíhá') ORDER BY j.deadline ASC, j.priority LIMIT 10""").fetchall()
        
        weather = get_weather_forecast()
        
        return jsonify({
            'success': True, 'date': target_date,
            'tasks': [dict(t) for t in tasks],
            'timesheets': [dict(ts) for ts in timesheets_today],
            'active_jobs': [dict(j) for j in active_jobs],
            'action_items': [], 'deliveries': [], 'conflicts': [],
            'weather': weather,
            'summary': {
                'tasks_count': len(tasks), 'action_items_count': 0,
                'deliveries_count': 0, 'conflicts_count': 0,
                'employees_working': len(set(ts['employee_id'] for ts in timesheets_today if ts['employee_id']))
            }
        })
    except Exception as e:
        print(f"[ERROR] Daily: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500

# ================================================================
# WEEK
# ================================================================
def get_planning_week():
    try:
        week_start = request.args.get('start')
        if week_start:
            week_start = datetime.fromisoformat(week_start).date()
        else:
            today = date.today()
            week_start = today - timedelta(days=today.weekday())
        
        db = get_db()
        employees = db.execute("""SELECT id, name, role, position FROM employees
            WHERE status = 'active' ORDER BY name ASC""").fetchall()
        
        week_data = []
        for day_offset in range(7):
            current_date = week_start + timedelta(days=day_offset)
            day_timesheets = db.execute("""SELECT ts.employee_id, ts.job_id, j.name as job_name,
                j.code as job_code, ts.hours as hours_planned, 'logged' as status
                FROM timesheets ts LEFT JOIN jobs j ON ts.job_id = j.id
                WHERE ts.date = ? ORDER BY ts.employee_id""", (current_date.isoformat(),)).fetchall()
            
            by_employee = {}
            for ts in day_timesheets:
                emp_id = ts['employee_id']
                if emp_id not in by_employee:
                    by_employee[emp_id] = []
                by_employee[emp_id].append(dict(ts))
            
            week_data.append({'date': current_date.isoformat(),
                            'day_name': current_date.strftime('%A'),
                            'assignments': by_employee})
        
        return jsonify({'success': True, 'week_start': week_start.isoformat(),
                       'employees': [dict(e) for e in employees], 'days': week_data})
    except Exception as e:
        print(f"[ERROR] Week: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500

# ================================================================
# COSTS
# ================================================================
def get_planning_costs(job_id=None):
    try:
        db = get_db()
        if job_id:
            job = db.execute("SELECT * FROM jobs WHERE id = ?", (job_id,)).fetchone()
            if not job:
                return jsonify({'success': False, 'error': 'Project not found'}), 404
            
            labor = db.execute("""SELECT SUM(ts.hours) as total_hours,
                SUM(ts.hours * COALESCE(e.hourly_rate, 0)) as total_labor_cost
                FROM timesheets ts LEFT JOIN employees e ON ts.employee_id = e.id
                WHERE ts.job_id = ?""", (job_id,)).fetchone()
            
            job_dict = dict(job)
            spent = labor['total_labor_cost'] or 0
            budget = job_dict.get('estimated_value') or job_dict.get('budget_labor') or 0
            job_dict.update({'budget': budget, 'spent': spent, 'hours_spent': labor['total_hours'] or 0,
                            'remaining': budget - spent, 'percent_used': (spent / budget * 100) if budget > 0 else 0,
                            'over_budget': spent > budget if budget > 0 else False})
            
            return jsonify({'success': True, 'project': job_dict})
        else:
            projects = db.execute("""SELECT j.id, j.name, j.code, j.status, j.estimated_value, j.actual_value,
                j.budget_labor, j.estimated_hours, j.actual_hours FROM jobs j
                WHERE j.status IN ('Plán', 'Probíhá') ORDER BY j.deadline ASC, j.priority""").fetchall()
            
            result = []
            for proj in projects:
                labor = db.execute("""SELECT SUM(ts.hours) as total_hours,
                    SUM(ts.hours * COALESCE(e.hourly_rate, 0)) as total_labor_cost
                    FROM timesheets ts LEFT JOIN employees e ON ts.employee_id = e.id
                    WHERE ts.job_id = ?""", (proj['id'],)).fetchone()
                
                proj_dict = dict(proj)
                spent = labor['total_labor_cost'] or 0
                budget = proj_dict.get('estimated_value') or proj_dict.get('budget_labor') or 0
                proj_dict.update({'budget': budget, 'spent': spent, 'hours_spent': labor['total_hours'] or 0,
                                'remaining': budget - spent, 'percent_used': (spent / budget * 100) if budget > 0 else 0,
                                'over_budget': spent > budget if budget > 0 else False})
                result.append(proj_dict)
            
            return jsonify({'success': True, 'projects': result})
    except Exception as e:
        print(f"[ERROR] Costs: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500

# ================================================================
# NOTIFICATIONS
# ================================================================
def get_planning_notifications():
    try:
        db = get_db()
        today = date.today()
        notifications = []
        
        overdue = db.execute("""SELECT COUNT(*) as count FROM tasks
            WHERE due_date < ? AND status != 'done'""", (today.isoformat(),)).fetchone()
        if overdue['count'] > 0:
            notifications.append({'type': 'warning', 'icon': '⚠️', 'title': 'Opožděné úkoly',
                                'message': f'{overdue["count"]} úkolů po termínu', 'link': '/tasks.html'})
        
        upcoming = db.execute("""SELECT COUNT(*) as count FROM tasks
            WHERE due_date BETWEEN ? AND ? AND status != 'done'""",
            (today.isoformat(), (today + timedelta(days=3)).isoformat())).fetchone()
        if upcoming['count'] > 0:
            notifications.append({'type': 'info', 'icon': '📅', 'title': 'Blížící se deadliny',
                                'message': f'{upcoming["count"]} úkolů v příštích 3 dnech', 'link': '/tasks.html'})
        
        no_deadline = db.execute("""SELECT COUNT(*) as count FROM jobs
            WHERE status IN ('Plán', 'Probíhá') AND deadline IS NULL""").fetchone()
        if no_deadline['count'] > 0:
            notifications.append({'type': 'info', 'icon': '📋', 'title': 'Zakázky bez termínu',
                                'message': f'{no_deadline["count"]} aktivních zakázek nemá deadline', 'link': '/jobs.html'})
        
        return jsonify({'success': True, 'notifications': notifications, 'count': len(notifications)})
    except Exception as e:
        print(f"[ERROR] Notifications: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

# ================================================================
# SUGGESTIONS
# ================================================================
def get_smart_suggestions():
    try:
        db = get_db()
        today = date.today()
        suggestions = []
        
        unassigned = db.execute("""SELECT t.id, t.title, t.job_id, j.name as job_name, t.due_date
            FROM tasks t LEFT JOIN jobs j ON t.job_id = j.id
            WHERE t.status != 'done' AND t.employee_id IS NULL AND t.due_date >= ?
            ORDER BY t.due_date ASC LIMIT 5""", (today.isoformat(),)).fetchall()
        if len(unassigned) > 0:
            suggestions.append({'type': 'assignment', 'priority': 'high',
                              'title': f'{len(unassigned)} úkolů bez přiřazení',
                              'description': 'Některé úkoly nemají přiřazeného zaměstnance',
                              'action': 'assign', 'tasks': [dict(t) for t in unassigned]})
        
        no_deadline = db.execute("""SELECT j.id, j.name, j.status, j.start_date FROM jobs j
            WHERE j.status IN ('Plán', 'Probíhá') AND j.deadline IS NULL LIMIT 5""").fetchall()
        if len(no_deadline) > 0:
            suggestions.append({'type': 'deadline', 'priority': 'medium',
                              'title': f'{len(no_deadline)} zakázek bez termínu',
                              'description': 'Aktivní zakázky by měly mít stanovený deadline',
                              'action': 'set_deadline', 'jobs': [dict(j) for j in no_deadline]})
        
        return jsonify({'success': True, 'suggestions': suggestions, 'count': len(suggestions)})
    except Exception as e:
        print(f"[ERROR] Suggestions: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

# Dummy functions for compatibility
def quick_complete_action_item(): return jsonify({'success': False, 'error': 'Not implemented'}), 501
def reschedule_task(): return jsonify({'success': False, 'error': 'Not implemented'}), 501
def get_employee_dashboard(employee_id): return jsonify({'success': False, 'error': 'Not implemented'}), 501
