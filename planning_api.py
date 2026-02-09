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

def get_weather_forecast(lat=49.69, lon=14.01):
    """Get weather with fallback to mock data"""
    if not REQUESTS_AVAILABLE or not WEATHER_API_KEY:
        return {
            'temp': 8, 'feels_like': 6, 'description': 'Zataženo',
            'icon': '04d', 'humidity': 75, 'wind_speed': 3.5,
            'rain_probability': 20, 'suitable_for_outdoor': True,
            'forecast_3h': [], 'is_mock': True
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
                                'rain_prob': round(item.get('pop', 0) * 100)} for item in data['list'][:8]],
                'is_mock': False
            }
    except:
        pass
    
    return {'temp': 10, 'description': 'Počasí nedostupné', 'suitable_for_outdoor': True, 'forecast_3h': [], 'is_mock': True}

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
            FROM jobs j WHERE j.status NOT IN ('cancelled', 'Zrušená', 'Dokončená') ORDER BY j.deadline ASC, j.priority""").fetchall()
        
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
        
        num_days = int(request.args.get('days', 7))
        num_days = max(1, min(num_days, 42))  # limit 1-42 dní
        week_data = []
        for day_offset in range(num_days):
            current_date = week_start + timedelta(days=day_offset)
            date_str = current_date.isoformat()
            
            # 1) Timesheets — skutečně odpracované hodiny
            day_timesheets = db.execute("""SELECT ts.employee_id, ts.job_id, j.name as job_name,
                j.code as job_code, ts.hours as hours_planned, 'logged' as status
                FROM timesheets ts LEFT JOIN jobs j ON ts.job_id = j.id
                WHERE ts.date = ? ORDER BY ts.employee_id""", (date_str,)).fetchall()
            
            by_employee = {}
            logged_keys = set()
            for ts in day_timesheets:
                emp_id = ts['employee_id']
                if emp_id not in by_employee:
                    by_employee[emp_id] = []
                by_employee[emp_id].append(dict(ts))
                logged_keys.add((emp_id, ts['job_id']))
            
            # 2) Day plans — plánovaná přiřazení (jen pokud nemají timesheet)
            try:
                day_plans = db.execute("""SELECT dp.employee_id, dp.job_id, j.name as job_name,
                    j.code as job_code, dp.planned_hours as hours_planned, dp.status
                    FROM day_plans dp LEFT JOIN jobs j ON dp.job_id = j.id
                    WHERE dp.date = ? AND dp.status != 'absent'
                    ORDER BY dp.employee_id""", (date_str,)).fetchall()
                
                for dp in day_plans:
                    emp_id = dp['employee_id']
                    key = (emp_id, dp['job_id'])
                    if key not in logged_keys:
                        if emp_id not in by_employee:
                            by_employee[emp_id] = []
                        entry = dict(dp)
                        entry['status'] = entry.get('status', 'planned')
                        by_employee[emp_id].append(entry)
                        logged_keys.add(key)
            except Exception as dp_err:
                print(f"[WARN] day_plans read: {dp_err}")
            
            week_data.append({'date': date_str,
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
            
            # Monthly trend — posledních 6 měsíců
            today = date.today()
            months_data = []
            month_names = ['Led','Úno','Bře','Dub','Kvě','Čer','Črc','Srp','Zář','Říj','Lis','Pro']
            
            for i in range(5, -1, -1):
                # Výpočet začátku měsíce (i měsíců zpět)
                if today.month - i <= 0:
                    year_offset = (i - today.month) // 12 + 1
                    month = 12 - ((i - today.month) % 12)
                    m_start = date(today.year - year_offset, month, 1)
                else:
                    m_start = date(today.year, today.month - i, 1)
                
                # Konec měsíce
                if m_start.month == 12:
                    m_end = date(m_start.year + 1, 1, 1)
                else:
                    m_end = date(m_start.year, m_start.month + 1, 1)
                
                monthly = db.execute("""
                    SELECT COALESCE(SUM(ts.hours * COALESCE(e.hourly_rate, 0)), 0) as cost
                    FROM timesheets ts
                    LEFT JOIN employees e ON ts.employee_id = e.id
                    WHERE ts.date >= ? AND ts.date < ?
                """, (m_start.isoformat(), m_end.isoformat())).fetchone()
                
                months_data.append({
                    'month': m_start.strftime('%m/%Y'),
                    'label': month_names[m_start.month - 1],
                    'cost': monthly['cost'] or 0
                })
            
            return jsonify({'success': True, 'projects': result, 'monthly_trend': months_data})
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
        
        # Sdílená proměnná pro týdenní dotazy
        week_ago = (today - timedelta(days=7)).isoformat()
        
        # 1) Detekce přetížení zaměstnanců — >40h za posledních 7 dní
        overloaded = db.execute("""
            SELECT e.id, e.name, SUM(ts.hours) as total_hours
            FROM timesheets ts
            JOIN employees e ON ts.employee_id = e.id
            WHERE ts.date >= ?
            GROUP BY e.id
            HAVING SUM(ts.hours) > 40
            ORDER BY total_hours DESC
        """, (week_ago,)).fetchall()
        for emp in overloaded:
            suggestions.append({
                'type': 'overload',
                'priority': 'high',
                'title': f'{emp["name"]} je přetížený ({emp["total_hours"]:.0f}h za týden)',
                'description': f'Zaměstnanec {emp["name"]} odpracoval {emp["total_hours"]:.0f}h za posledních 7 dní (limit 40h). Zvažte přerozdělení práce.',
                'action': 'redistribute',
                'employee_id': emp['id']
            })
        
        # 2) Nerovnoměrné vytížení týmu
        week_hours = db.execute("""
            SELECT e.id, e.name, COALESCE(SUM(ts.hours), 0) as total_hours
            FROM employees e
            LEFT JOIN timesheets ts ON ts.employee_id = e.id AND ts.date >= ?
            WHERE e.status = 'active'
            GROUP BY e.id
            HAVING total_hours > 0
            ORDER BY total_hours DESC
        """, (week_ago,)).fetchall()
        if len(week_hours) >= 2:
            max_emp = week_hours[0]
            min_emp = week_hours[-1]
            if min_emp['total_hours'] > 0 and max_emp['total_hours'] >= 3 * min_emp['total_hours']:
                suggestions.append({
                    'type': 'imbalance',
                    'priority': 'medium',
                    'title': 'Nerovnoměrné vytížení týmu',
                    'description': f'{max_emp["name"]} má {max_emp["total_hours"]:.0f}h, zatímco {min_emp["name"]} pouze {min_emp["total_hours"]:.0f}h za poslední týden.',
                    'action': 'balance',
                    'details': {
                        'most_loaded': {'id': max_emp['id'], 'name': max_emp['name'], 'hours': max_emp['total_hours']},
                        'least_loaded': {'id': min_emp['id'], 'name': min_emp['name'], 'hours': min_emp['total_hours']}
                    }
                })
        
        # 3) Zakázky bez úkolů
        jobs_no_tasks = db.execute("""
            SELECT j.id, j.name, j.code, j.status, j.deadline
            FROM jobs j
            LEFT JOIN tasks t ON t.job_id = j.id
            WHERE j.status IN ('Plán', 'Probíhá')
            GROUP BY j.id
            HAVING COUNT(t.id) = 0
            ORDER BY j.deadline ASC
            LIMIT 10
        """).fetchall()
        if len(jobs_no_tasks) > 0:
            suggestions.append({
                'type': 'no_tasks',
                'priority': 'medium',
                'title': f'{len(jobs_no_tasks)} zakázek bez úkolů',
                'description': 'Aktivní zakázky bez rozplánovaných úkolů — nelze sledovat postup.',
                'action': 'create_tasks',
                'jobs': [dict(j) for j in jobs_no_tasks]
            })
        
        # 4) Zakázky co pravděpodobně nestihnou deadline
        three_days = (today + timedelta(days=3)).isoformat()
        at_risk = db.execute("""
            SELECT j.id, j.name, j.code, j.deadline, j.progress,
                   COALESCE(j.progress, 0) as completion_percentage
            FROM jobs j
            WHERE j.status IN ('Plán', 'Probíhá')
              AND j.deadline IS NOT NULL
              AND j.deadline <= ?
              AND j.deadline >= ?
              AND COALESCE(j.progress, 0) < 50
            ORDER BY j.deadline ASC
        """, (three_days, today.isoformat())).fetchall()
        for job in at_risk:
            days_left = (date.fromisoformat(job['deadline']) - today).days
            suggestions.append({
                'type': 'deadline_risk',
                'priority': 'urgent',
                'title': f'Zakázka "{job["name"]}" pravděpodobně nestihne deadline',
                'description': f'Zbývá {days_left} dní do deadline, ale progress je jen {job["completion_percentage"]:.0f}%. Vyžaduje okamžitou pozornost.',
                'action': 'expedite',
                'job_id': job['id'],
                'job_name': job['name'],
                'days_remaining': days_left,
                'progress': job['completion_percentage']
            })
        
        # Řazení podle priority: urgent → high → medium → low
        priority_order = {'urgent': 0, 'high': 1, 'medium': 2, 'low': 3}
        suggestions.sort(key=lambda s: priority_order.get(s.get('priority', 'low'), 99))
        
        return jsonify({'success': True, 'suggestions': suggestions, 'count': len(suggestions)})
    except Exception as e:
        print(f"[ERROR] Suggestions: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

# ================================================================
# DAY PLANNING SYSTEM
# ================================================================

def get_day_plans(target_date=None):
    """Vrátí plány pro daný den"""
    try:
        if not target_date:
            target_date = request.args.get('date', date.today().isoformat())
        db = get_db()
        
        plans = db.execute("""
            SELECT dp.id, dp.date, dp.employee_id, dp.job_id, 
                   dp.planned_hours, dp.actual_hours, dp.status, dp.note,
                   dp.confirmed_at,
                   e.name as employee_name, e.role as employee_role,
                   j.name as job_name, j.code as job_code
            FROM day_plans dp
            LEFT JOIN employees e ON dp.employee_id = e.id
            LEFT JOIN jobs j ON dp.job_id = j.id
            WHERE dp.date = ?
            ORDER BY e.name, dp.id
        """, (target_date,)).fetchall()
        
        return jsonify({
            'success': True,
            'date': target_date,
            'plans': [dict(p) for p in plans]
        })
    except Exception as e:
        print(f"[ERROR] get_day_plans: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

def create_day_plan():
    """Vytvoří nové přiřazení zaměstnance na den"""
    try:
        data = request.get_json(force=True, silent=True) or {}
        target_date = data.get('date', date.today().isoformat())
        employee_id = data.get('employee_id')
        job_id = data.get('job_id')
        planned_hours = float(data.get('planned_hours', 8.0))
        status = data.get('status', 'planned')
        note = data.get('note', '')
        
        if not employee_id:
            return jsonify({'success': False, 'error': 'employee_id je povinný'}), 400
        
        valid_statuses = ['planned', 'confirmed', 'absent', 'sick', 'vacation', 'uncertain']
        if status not in valid_statuses:
            status = 'planned'
        
        db = get_db()
        cursor = db.execute("""
            INSERT INTO day_plans (date, employee_id, job_id, planned_hours, status, note)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (target_date, int(employee_id), int(job_id) if job_id else None, planned_hours, status, note))
        db.commit()
        
        return jsonify({'success': True, 'id': cursor.lastrowid})
    except Exception as e:
        print(f"[ERROR] create_day_plan: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

def update_day_plan(plan_id):
    """Aktualizuje plán"""
    try:
        data = request.get_json(force=True, silent=True) or {}
        db = get_db()
        
        allowed = ['job_id', 'planned_hours', 'actual_hours', 'status', 'note']
        sets = []
        vals = []
        for k in allowed:
            if k in data:
                v = data[k]
                if k in ('planned_hours', 'actual_hours') and v is not None:
                    v = float(v)
                if k == 'job_id' and v is not None:
                    v = int(v)
                if k == 'status' and v not in ['planned', 'confirmed', 'absent', 'sick', 'vacation', 'uncertain']:
                    continue
                sets.append(f"{k}=?")
                vals.append(v)
        
        if sets:
            vals.append(int(plan_id))
            db.execute("UPDATE day_plans SET " + ", ".join(sets) + " WHERE id=?", vals)
            db.commit()
        
        return jsonify({'success': True})
    except Exception as e:
        print(f"[ERROR] update_day_plan: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

def delete_day_plan(plan_id):
    """Smaže plán"""
    try:
        db = get_db()
        db.execute("DELETE FROM day_plans WHERE id=?", (int(plan_id),))
        db.commit()
        return jsonify({'success': True})
    except Exception as e:
        print(f"[ERROR] delete_day_plan: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

def delete_timesheet_by_day():
    """Smaže timesheet záznamy pro zaměstnance/den/zakázku"""
    try:
        data = request.get_json(force=True, silent=True) or {}
        target_date = data.get('date')
        employee_id = data.get('employee_id')
        job_id = data.get('job_id')
        
        if not target_date or not employee_id:
            return jsonify({'success': False, 'error': 'date a employee_id jsou povinné'}), 400
        
        db = get_db()
        if job_id:
            db.execute("DELETE FROM timesheets WHERE date=? AND employee_id=? AND job_id=?",
                       (target_date, int(employee_id), int(job_id)))
        else:
            db.execute("DELETE FROM timesheets WHERE date=? AND employee_id=?",
                       (target_date, int(employee_id)))
        db.commit()
        return jsonify({'success': True})
    except Exception as e:
        print(f"[ERROR] delete_timesheet_by_day: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

def confirm_day_plans():
    """Potvrdí plány a vytvoří výkazy"""
    try:
        data = request.get_json(force=True, silent=True) or {}
        confirmations = data.get('confirmations', [])
        
        if not confirmations:
            return jsonify({'success': False, 'error': 'Žádná data k potvrzení'}), 400
        
        db = get_db()
        created_timesheets = 0
        
        for conf in confirmations:
            plan_id = conf.get('id')
            actual_hours = conf.get('actual_hours')
            note = conf.get('note', '')
            status = conf.get('status', 'confirmed')
            
            if not plan_id:
                continue
            
            plan = db.execute("SELECT * FROM day_plans WHERE id=?", (int(plan_id),)).fetchone()
            if not plan:
                continue
            
            actual_h = float(actual_hours) if actual_hours is not None else plan['planned_hours']
            db.execute("""
                UPDATE day_plans SET actual_hours=?, status=?, note=?, confirmed_at=datetime('now')
                WHERE id=?
            """, (actual_h, status, note or plan['note'], int(plan_id)))
            
            if status == 'confirmed' and actual_h > 0 and plan['job_id']:
                existing = db.execute("""
                    SELECT id FROM timesheets 
                    WHERE employee_id=? AND job_id=? AND date=?
                """, (plan['employee_id'], plan['job_id'], plan['date'])).fetchone()
                
                if not existing:
                    db.execute("""
                        INSERT INTO timesheets (employee_id, job_id, date, hours, note)
                        VALUES (?, ?, ?, ?, ?)
                    """, (plan['employee_id'], plan['job_id'], plan['date'], actual_h, note or ''))
                    created_timesheets += 1
                else:
                    db.execute("""
                        UPDATE timesheets SET hours=?, note=? WHERE id=?
                    """, (actual_h, note or '', existing['id']))
        
        db.commit()
        return jsonify({'success': True, 'created_timesheets': created_timesheets})
    except Exception as e:
        print(f"[ERROR] confirm_day_plans: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500

def copy_day_plans():
    """Zkopíruje plány z jednoho dne na jiný"""
    try:
        data = request.get_json(force=True, silent=True) or {}
        from_date = data.get('from_date')
        to_date = data.get('to_date')
        
        if not from_date or not to_date:
            return jsonify({'success': False, 'error': 'from_date a to_date jsou povinné'}), 400
        
        db = get_db()
        
        db.execute("DELETE FROM day_plans WHERE date=? AND status='planned'", (to_date,))
        
        plans = db.execute("""
            SELECT employee_id, job_id, planned_hours, note 
            FROM day_plans WHERE date=? AND status NOT IN ('absent', 'sick', 'vacation')
        """, (from_date,)).fetchall()
        
        for p in plans:
            db.execute("""
                INSERT INTO day_plans (date, employee_id, job_id, planned_hours, status, note)
                VALUES (?, ?, ?, ?, 'planned', ?)
            """, (to_date, p['employee_id'], p['job_id'], p['planned_hours'], p['note'] or ''))
        
        db.commit()
        return jsonify({'success': True, 'copied': len(plans)})
    except Exception as e:
        print(f"[ERROR] copy_day_plans: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

# Dummy functions for compatibility
def quick_complete_action_item(): return jsonify({'success': False, 'error': 'Not implemented'}), 501
def reschedule_task(): return jsonify({'success': False, 'error': 'Not implemented'}), 501
def get_employee_dashboard(employee_id): return jsonify({'success': False, 'error': 'Not implemented'}), 501
