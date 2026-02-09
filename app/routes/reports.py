# Green David App
from flask import Blueprint, jsonify, request, send_from_directory
from datetime import datetime, timedelta
from app.database import get_db
from app.utils.permissions import require_auth, require_role, requires_role

reports_bp = Blueprint('reports', __name__)


@reports_bp.route("/reports")
@reports_bp.route("/reports-hub")
def reports_hub():
    return send_from_directory(".", "reports.html")


@reports_bp.route("/reports-daily")
def reports_daily():
    return send_from_directory(".", "reports-daily.html")


@reports_bp.route("/reports-week")
def reports_week():
    return send_from_directory(".", "reports-week.html")


@reports_bp.route("/reports-project")
def reports_project():
    return send_from_directory(".", "reports-project.html")


# Reports routes from main.py
@reports_bp.route("/reports.html")
def page_reports():
    return send_from_directory(".", "reports.html")

# ----------------- Job detail UI routes -----------------
@reports_bp.route("/api/admin/download-db", methods=["GET"])
@requires_role('owner', 'admin')
def api_admin_download_db():
    """Stáhne aktuální SQLite databázi jako soubor (pouze owner/admin)."""
    db_path = os.environ.get("DB_PATH") or "/var/data/app.db"
    if not os.path.exists(db_path):
        return jsonify({"ok": False, "error": "db_not_found", "path": db_path}), 404
    return send_file(db_path, as_attachment=True, download_name="app.db")


# Additional routes from main.py
@reports_bp.route("/search", methods=["GET"])
def search_page():
    q = (request.args.get("q") or "").strip()
    results = []
    if q:
        like = f"%{q}%"
        db = get_db()
        try:
            # Use title column if available, fallback to name
            title_col = _job_title_col()
            cur = db.execute(f"SELECT id, {title_col} AS title, city, code, date FROM jobs WHERE ({title_col} LIKE ? COLLATE NOCASE OR city LIKE ? COLLATE NOCASE OR code LIKE ? COLLATE NOCASE) ORDER BY id DESC LIMIT 50", (like, like, like))
            for r in cur.fetchall():
                results.append({"type":"Zakázka","id":r["id"],"title":r["title"] or "", "sub":" • ".join([x for x in [r["city"], r["code"]] if x]),"date":r["date"],"url": f"/?tab=jobs&jobId={r['id']}"})
        except Exception: pass
        try:
            cur = db.execute("SELECT id, name, role FROM employees WHERE (name LIKE ? COLLATE NOCASE OR role LIKE ? COLLATE NOCASE) ORDER BY id DESC LIMIT 50", (like, like))
            for r in cur.fetchall():
                results.append({"type":"Zaměstnanec","id":r["id"],"title":r["name"],"sub":r["role"] or "","date":"","url": "/?tab=employees"})
        except Exception: pass
    return render_template("search.html", title="Hledání", q=q, results=results)

# ----------------- Calendar API -----------------
@reports_bp.route('/api/reports/generate', methods=['POST'])
def api_generate_report():
    """Generate comprehensive report with real data from all modules"""
    u, err = require_role()
    if err: return err
    
    try:
        data = request.get_json() or {}
        report_type = data.get('type', 'weekly')
        date_from = data.get('dateFrom')
        date_to = data.get('dateTo')
        project_id = data.get('projectId')
        content_sections = data.get('content', [])
        detail_sections = data.get('details', [])
        export_format = data.get('format', 'json')
        
        # Filtry zaměstnanců a zakázek
        employee_ids = data.get('employeeIds')  # None = všichni, [] = žádní, [1,2] = konkrétní
        job_ids = data.get('jobIds')  # None = všechny, [] = žádné, [1,2] = konkrétní
        
        db = get_db()
        report_data = {
            'type': report_type,
            'generated_at': datetime.now().isoformat(),
            'date_from': date_from,
            'date_to': date_to,
            'filters': {
                'employees': employee_ids,
                'jobs': job_ids
            },
            'sections': {},
            'summary': {}
        }
        
        # Helper pro employee filter
        def emp_filter_sql(prefix=''):
            if not employee_ids:
                return '', []
            placeholders = ','.join(['?' for _ in employee_ids])
            return f' AND {prefix}employee_id IN ({placeholders})', employee_ids
        
        # Helper pro job filter
        def job_filter_sql(prefix='', col='job_id'):
            if not job_ids:
                return '', []
            placeholders = ','.join(['?' for _ in job_ids])
            return f' AND {prefix}{col} IN ({placeholders})', job_ids
        
        # ============================================================
        # WEEKLY REPORT - Týdenní přehled
        # ============================================================
        if report_type == 'weekly':
            
            # Hodiny - souhrn
            if 'hours_summary' in content_sections:
                try:
                    emp_sql, emp_params = emp_filter_sql()
                    job_sql, job_params = job_filter_sql()
                    result = db.execute(f'''
                        SELECT 
                            COALESCE(SUM(hours), 0) as total_hours,
                            COUNT(DISTINCT employee_id) as unique_employees,
                            COUNT(DISTINCT job_id) as unique_jobs,
                            COUNT(*) as total_entries
                        FROM timesheets
                        WHERE date BETWEEN ? AND ?
                        {emp_sql} {job_sql}
                    ''', (date_from, date_to) + tuple(emp_params) + tuple(job_params)).fetchone()
                    report_data['sections']['hours_summary'] = {
                        'total_hours': round(result['total_hours'] or 0, 1),
                        'unique_employees': result['unique_employees'] or 0,
                        'unique_jobs': result['unique_jobs'] or 0,
                        'total_entries': result['total_entries'] or 0
                    }
                except Exception as e:
                    report_data['sections']['hours_summary'] = {'error': str(e)}
            
            # Hodiny dle projektů
            if 'hours_by_project' in content_sections:
                try:
                    rows = db.execute('''
                        SELECT 
                            j.id, 
                            COALESCE(j.name, j.title, 'Bez názvu') as project_name,
                            j.client,
                            j.status,
                            COALESCE(SUM(t.hours), 0) as hours,
                            COUNT(DISTINCT t.employee_id) as workers
                        FROM jobs j
                        LEFT JOIN timesheets t ON t.job_id = j.id AND t.date BETWEEN ? AND ?
                        GROUP BY j.id
                        HAVING hours > 0
                        ORDER BY hours DESC
                    ''', (date_from, date_to)).fetchall()
                    report_data['sections']['hours_by_project'] = [
                        {'id': r['id'], 'name': r['project_name'], 'client': r['client'] or '-', 
                         'status': r['status'], 'hours': round(r['hours'], 1), 'workers': r['workers']}
                        for r in rows
                    ]
                except Exception as e:
                    report_data['sections']['hours_by_project'] = []
            
            # Hodiny dle zaměstnanců
            if 'hours_by_employee' in content_sections:
                try:
                    rows = db.execute('''
                        SELECT 
                            e.id,
                            e.name,
                            e.role,
                            COALESCE(SUM(t.hours), 0) as hours,
                            COUNT(DISTINCT t.job_id) as projects,
                            COUNT(DISTINCT t.date) as days_worked
                        FROM employees e
                        LEFT JOIN timesheets t ON t.employee_id = e.id AND t.date BETWEEN ? AND ?
                        WHERE e.active = 1
                        GROUP BY e.id
                        HAVING hours > 0
                        ORDER BY hours DESC
                    ''', (date_from, date_to)).fetchall()
                    report_data['sections']['hours_by_employee'] = [
                        {'id': r['id'], 'name': r['name'], 'role': r['role'] or '-',
                         'hours': round(r['hours'], 1), 'projects': r['projects'], 'days': r['days_worked']}
                        for r in rows
                    ]
                except Exception as e:
                    report_data['sections']['hours_by_employee'] = []
            
            # Dokončené úkoly
            if 'tasks_completed' in content_sections:
                try:
                    rows = db.execute('''
                        SELECT 
                            t.id, t.title, t.status,
                            COALESCE(j.name, j.title, '-') as job_name,
                            e.name as assignee
                        FROM tasks t
                        LEFT JOIN jobs j ON j.id = t.job_id
                        LEFT JOIN employees e ON e.id = t.employee_id
                        WHERE t.status IN ('done', 'completed', 'Dokončeno')
                        AND t.created_at BETWEEN ? AND ?
                        ORDER BY t.id DESC
                        LIMIT 50
                    ''', (date_from, date_to + ' 23:59:59')).fetchall()
                    report_data['sections']['tasks_completed'] = [dict(r) for r in rows]
                except Exception as e:
                    report_data['sections']['tasks_completed'] = []
            
            # Rozpracované úkoly
            if 'tasks_pending' in content_sections:
                try:
                    rows = db.execute('''
                        SELECT 
                            t.id, t.title, t.status, t.due_date,
                            COALESCE(j.name, j.title, '-') as job_name,
                            e.name as assignee
                        FROM tasks t
                        LEFT JOIN jobs j ON j.id = t.job_id
                        LEFT JOIN employees e ON e.id = t.employee_id
                        WHERE t.status IN ('open', 'in_progress', 'Otevřený', 'V práci')
                        ORDER BY t.due_date ASC, t.id DESC
                        LIMIT 50
                    ''').fetchall()
                    report_data['sections']['tasks_pending'] = [dict(r) for r in rows]
                except Exception as e:
                    report_data['sections']['tasks_pending'] = []
            
            # Úkoly po termínu
            if 'tasks_overdue' in content_sections:
                try:
                    rows = db.execute('''
                        SELECT 
                            t.id, t.title, t.status, t.due_date,
                            COALESCE(j.name, j.title, '-') as job_name,
                            e.name as assignee,
                            julianday('now') - julianday(t.due_date) as days_overdue
                        FROM tasks t
                        LEFT JOIN jobs j ON j.id = t.job_id
                        LEFT JOIN employees e ON e.id = t.employee_id
                        WHERE t.due_date < date('now')
                        AND t.status NOT IN ('done', 'completed', 'Dokončeno', 'cancelled')
                        ORDER BY t.due_date ASC
                    ''').fetchall()
                    report_data['sections']['tasks_overdue'] = [
                        {**dict(r), 'days_overdue': int(r['days_overdue'] or 0)}
                        for r in rows
                    ]
                except Exception as e:
                    report_data['sections']['tasks_overdue'] = []
            
            # Denní breakdown (detaily)
            if 'daily_breakdown' in detail_sections:
                try:
                    rows = db.execute('''
                        SELECT 
                            date,
                            SUM(hours) as hours,
                            COUNT(DISTINCT employee_id) as workers,
                            COUNT(DISTINCT job_id) as projects
                        FROM timesheets
                        WHERE date BETWEEN ? AND ?
                        GROUP BY date
                        ORDER BY date
                    ''', (date_from, date_to)).fetchall()
                    report_data['sections']['daily_breakdown'] = [
                        {'date': r['date'], 'hours': round(r['hours'], 1), 
                         'workers': r['workers'], 'projects': r['projects']}
                        for r in rows
                    ]
                except Exception as e:
                    report_data['sections']['daily_breakdown'] = []
            
            # Issues/problémy
            if 'issues_reported' in detail_sections:
                try:
                    rows = db.execute('''
                        SELECT 
                            i.id, i.title, i.status, i.severity, i.type,
                            COALESCE(j.name, j.title, '-') as job_name,
                            e.name as assigned_to
                        FROM issues i
                        LEFT JOIN jobs j ON j.id = i.job_id
                        LEFT JOIN employees e ON e.id = i.assigned_to
                        WHERE i.created_at BETWEEN ? AND ?
                        ORDER BY i.created_at DESC
                    ''', (date_from, date_to + ' 23:59:59')).fetchall()
                    report_data['sections']['issues'] = [dict(r) for r in rows]
                except Exception as e:
                    report_data['sections']['issues'] = []
        
        # ============================================================
        # MONTHLY REPORT - Měsíční přehled
        # ============================================================
        elif report_type == 'monthly':
            
            # Finanční přehled
            if 'financial' in content_sections:
                try:
                    # Celkové hodiny a náklady na práci
                    labor = db.execute('''
                        SELECT 
                            COALESCE(SUM(t.hours), 0) as total_hours,
                            COALESCE(SUM(t.hours * COALESCE(e.hourly_rate, 200)), 0) as labor_cost
                        FROM timesheets t
                        LEFT JOIN employees e ON e.id = t.employee_id
                        WHERE t.date BETWEEN ? AND ?
                    ''', (date_from, date_to)).fetchone()
                    
                    # Počet zakázek dle statusu
                    jobs_stats = db.execute('''
                        SELECT 
                            COUNT(*) as total_jobs,
                            SUM(CASE WHEN status IN ('completed', 'Dokončeno', 'done') THEN 1 ELSE 0 END) as completed,
                            SUM(CASE WHEN status IN ('active', 'Aktivní', 'V práci') THEN 1 ELSE 0 END) as active
                        FROM jobs
                    ''').fetchone()
                    
                    report_data['sections']['financial'] = {
                        'total_hours': round(labor['total_hours'] or 0, 1),
                        'labor_cost': round(labor['labor_cost'] or 0, 0),
                        'total_jobs': jobs_stats['total_jobs'] or 0,
                        'completed_jobs': jobs_stats['completed'] or 0,
                        'active_jobs': jobs_stats['active'] or 0
                    }
                except Exception as e:
                    report_data['sections']['financial'] = {'error': str(e)}
            
            # Top projekty
            if 'top_projects' in content_sections:
                try:
                    rows = db.execute('''
                        SELECT 
                            j.id,
                            COALESCE(j.name, j.title, 'Bez názvu') as name,
                            j.client,
                            j.status,
                            COALESCE(SUM(t.hours), 0) as hours,
                            COUNT(DISTINCT t.employee_id) as workers,
                            COALESCE(SUM(t.hours * COALESCE(e.hourly_rate, 200)), 0) as cost
                        FROM jobs j
                        LEFT JOIN timesheets t ON t.job_id = j.id AND t.date BETWEEN ? AND ?
                        LEFT JOIN employees e ON e.id = t.employee_id
                        GROUP BY j.id
                        ORDER BY hours DESC
                        LIMIT 15
                    ''', (date_from, date_to)).fetchall()
                    report_data['sections']['top_projects'] = [
                        {'id': r['id'], 'name': r['name'], 'client': r['client'] or '-',
                         'status': r['status'], 'hours': round(r['hours'], 1), 
                         'workers': r['workers'], 'cost': round(r['cost'], 0)}
                        for r in rows
                    ]
                except Exception as e:
                    report_data['sections']['top_projects'] = []
            
            # Produktivita týmu
            if 'productivity' in content_sections:
                try:
                    rows = db.execute('''
                        SELECT 
                            e.id, e.name, e.role,
                            COALESCE(e.hourly_rate, 200) as hourly_rate,
                            COALESCE(SUM(t.hours), 0) as hours,
                            COUNT(DISTINCT t.job_id) as projects,
                            COUNT(DISTINCT t.date) as days_worked
                        FROM employees e
                        LEFT JOIN timesheets t ON t.employee_id = e.id AND t.date BETWEEN ? AND ?
                        WHERE e.active = 1
                        GROUP BY e.id
                        ORDER BY hours DESC
                    ''', (date_from, date_to)).fetchall()
                    report_data['sections']['productivity'] = [
                        {'id': r['id'], 'name': r['name'], 'role': r['role'] or '-',
                         'hourly_rate': r['hourly_rate'], 'hours': round(r['hours'], 1),
                         'projects': r['projects'], 'days': r['days_worked'],
                         'earnings': round(r['hours'] * r['hourly_rate'], 0)}
                        for r in rows
                    ]
                except Exception as e:
                    report_data['sections']['productivity'] = []
            
            # Sklad - stav
            if 'warehouse' in content_sections:
                try:
                    rows = db.execute('''
                        SELECT 
                            id, name, category, quantity, unit, min_quantity,
                            COALESCE(unit_price, 0) as unit_price
                        FROM warehouse_items
                        ORDER BY category, name
                    ''').fetchall()
                    total_value = sum(r['quantity'] * r['unit_price'] for r in rows)
                    low_stock = [r for r in rows if r['min_quantity'] and r['quantity'] <= r['min_quantity']]
                    
                    report_data['sections']['warehouse'] = {
                        'total_items': len(rows),
                        'total_value': round(total_value, 0),
                        'low_stock_count': len(low_stock),
                        'items': [dict(r) for r in rows[:30]]
                    }
                except Exception as e:
                    report_data['sections']['warehouse'] = {'total_items': 0, 'items': []}
            
            # Rozpad příjmů dle projektů
            if 'revenue' in content_sections:
                try:
                    rows = db.execute('''
                        SELECT 
                            j.id,
                            COALESCE(j.name, j.title, 'Bez názvu') as name,
                            j.client,
                            COALESCE(j.budget, 0) as budget,
                            COALESCE(SUM(t.hours * COALESCE(e.hourly_rate, 200)), 0) as labor_cost,
                            COALESCE(j.budget, 0) - COALESCE(SUM(t.hours * COALESCE(e.hourly_rate, 200)), 0) as margin
                        FROM jobs j
                        LEFT JOIN timesheets t ON t.job_id = j.id AND t.date BETWEEN ? AND ?
                        LEFT JOIN employees e ON e.id = t.employee_id
                        WHERE j.budget > 0
                        GROUP BY j.id
                        ORDER BY j.budget DESC
                        LIMIT 20
                    ''', (date_from, date_to)).fetchall()
                    report_data['sections']['revenue'] = [
                        {'id': r['id'], 'name': r['name'], 'client': r['client'] or '-',
                         'budget': round(r['budget'], 0), 'labor_cost': round(r['labor_cost'], 0),
                         'margin': round(r['margin'], 0)}
                        for r in rows
                    ]
                except Exception as e:
                    report_data['sections']['revenue'] = {'info': 'Data nejsou k dispozici - vyžaduje rozpočty u zakázek'}
            
            # Rozpad nákladů
            if 'costs' in content_sections:
                try:
                    # Náklady na práci
                    labor = db.execute('''
                        SELECT COALESCE(SUM(t.hours * COALESCE(e.hourly_rate, 200)), 0) as total
                        FROM timesheets t
                        LEFT JOIN employees e ON e.id = t.employee_id
                        WHERE t.date BETWEEN ? AND ?
                    ''', (date_from, date_to)).fetchone()
                    
                    # Spotřeba materiálu (z job_materials)
                    materials = db.execute('''
                        SELECT COALESCE(SUM(jm.qty * COALESCE(wi.unit_price, 0)), 0) as total
                        FROM job_materials jm
                        LEFT JOIN warehouse_items wi ON wi.name = jm.name
                        LEFT JOIN jobs j ON j.id = jm.job_id
                    ''').fetchone()
                    
                    report_data['sections']['costs'] = {
                        'labor_cost': round(labor['total'] or 0, 0),
                        'materials_cost': round(materials['total'] or 0, 0),
                        'total_cost': round((labor['total'] or 0) + (materials['total'] or 0), 0)
                    }
                except Exception as e:
                    report_data['sections']['costs'] = {'info': 'Data nejsou k dispozici'}
            
            # Ziskovost
            if 'profitability' in content_sections:
                try:
                    # Celkové příjmy (rozpočty dokončených zakázek)
                    revenue = db.execute('''
                        SELECT COALESCE(SUM(budget), 0) as total
                        FROM jobs
                        WHERE status IN ('completed', 'Dokončeno', 'done')
                    ''').fetchone()
                    
                    # Celkové náklady
                    costs = db.execute('''
                        SELECT COALESCE(SUM(t.hours * COALESCE(e.hourly_rate, 200)), 0) as total
                        FROM timesheets t
                        LEFT JOIN employees e ON e.id = t.employee_id
                        WHERE t.date BETWEEN ? AND ?
                    ''', (date_from, date_to)).fetchone()
                    
                    total_revenue = revenue['total'] or 0
                    total_costs = costs['total'] or 0
                    profit = total_revenue - total_costs
                    margin = (profit / total_revenue * 100) if total_revenue > 0 else 0
                    
                    report_data['sections']['profitability'] = {
                        'total_revenue': round(total_revenue, 0),
                        'total_costs': round(total_costs, 0),
                        'profit': round(profit, 0),
                        'margin_percent': round(margin, 1)
                    }
                except Exception as e:
                    report_data['sections']['profitability'] = {'info': 'Data nejsou k dispozici - vyžaduje rozpočty u zakázek'}
            
            # Přehled klientů
            if 'clients' in content_sections:
                try:
                    rows = db.execute('''
                        SELECT 
                            j.client,
                            COUNT(DISTINCT j.id) as jobs_count,
                            COALESCE(SUM(j.budget), 0) as total_budget,
                            COALESCE(SUM(t.hours), 0) as total_hours
                        FROM jobs j
                        LEFT JOIN timesheets t ON t.job_id = j.id AND t.date BETWEEN ? AND ?
                        WHERE j.client IS NOT NULL AND j.client != ''
                        GROUP BY j.client
                        ORDER BY total_budget DESC
                        LIMIT 20
                    ''', (date_from, date_to)).fetchall()
                    report_data['sections']['clients'] = [
                        {'client': r['client'], 'jobs_count': r['jobs_count'],
                         'total_budget': round(r['total_budget'], 0), 'total_hours': round(r['total_hours'], 1)}
                        for r in rows
                    ]
                except Exception as e:
                    report_data['sections']['clients'] = {'info': 'Data nejsou k dispozici'}
            
            # Srovnání s minulým obdobím
            if 'comparison' in content_sections:
                try:
                    df = datetime.strptime(date_from, '%Y-%m-%d')
                    dt = datetime.strptime(date_to, '%Y-%m-%d')
                    period_days = (dt - df).days + 1
                    prev_from = (df - timedelta(days=period_days)).strftime('%Y-%m-%d')
                    prev_to = (df - timedelta(days=1)).strftime('%Y-%m-%d')
                    
                    # Aktuální období
                    current = db.execute('''
                        SELECT COALESCE(SUM(hours), 0) as hours, COUNT(DISTINCT job_id) as jobs
                        FROM timesheets WHERE date BETWEEN ? AND ?
                    ''', (date_from, date_to)).fetchone()
                    
                    # Předchozí období
                    previous = db.execute('''
                        SELECT COALESCE(SUM(hours), 0) as hours, COUNT(DISTINCT job_id) as jobs
                        FROM timesheets WHERE date BETWEEN ? AND ?
                    ''', (prev_from, prev_to)).fetchone()
                    
                    curr_hours = current['hours'] or 0
                    prev_hours = previous['hours'] or 0
                    hours_change = ((curr_hours - prev_hours) / prev_hours * 100) if prev_hours > 0 else 0
                    
                    report_data['sections']['comparison'] = {
                        'current_hours': round(curr_hours, 1),
                        'previous_hours': round(prev_hours, 1),
                        'hours_change_percent': round(hours_change, 1),
                        'current_jobs': current['jobs'] or 0,
                        'previous_jobs': previous['jobs'] or 0
                    }
                except Exception as e:
                    report_data['sections']['comparison'] = {'info': 'Data nejsou k dispozici'}
            
            # Detail nákladů - Náklady na zaměstnance
            if 'salaries' in detail_sections:
                try:
                    rows = db.execute('''
                        SELECT 
                            e.id, e.name, e.role,
                            COALESCE(e.hourly_rate, 200) as hourly_rate,
                            COALESCE(SUM(t.hours), 0) as hours,
                            COALESCE(SUM(t.hours * COALESCE(e.hourly_rate, 200)), 0) as total_cost
                        FROM employees e
                        LEFT JOIN timesheets t ON t.employee_id = e.id AND t.date BETWEEN ? AND ?
                        WHERE e.active = 1
                        GROUP BY e.id
                        HAVING hours > 0
                        ORDER BY total_cost DESC
                    ''', (date_from, date_to)).fetchall()
                    report_data['sections']['salaries'] = [
                        {'name': r['name'], 'role': r['role'] or '-', 'hourly_rate': r['hourly_rate'],
                         'hours': round(r['hours'], 1), 'total_cost': round(r['total_cost'], 0)}
                        for r in rows
                    ]
                except Exception as e:
                    report_data['sections']['salaries'] = []
            
            # Detail nákladů - Náklady na materiál
            if 'materials' in detail_sections:
                try:
                    rows = db.execute('''
                        SELECT 
                            jm.name, jm.qty, jm.unit,
                            COALESCE(wi.unit_price, 0) as unit_price,
                            jm.qty * COALESCE(wi.unit_price, 0) as total_price,
                            COALESCE(j.name, j.title, '-') as job_name
                        FROM job_materials jm
                        LEFT JOIN warehouse_items wi ON wi.name = jm.name
                        LEFT JOIN jobs j ON j.id = jm.job_id
                        ORDER BY total_price DESC
                        LIMIT 50
                    ''').fetchall()
                    report_data['sections']['materials'] = [
                        {'name': r['name'], 'qty': r['qty'], 'unit': r['unit'] or 'ks',
                         'unit_price': round(r['unit_price'], 0), 'total_price': round(r['total_price'], 0),
                         'job_name': r['job_name']}
                        for r in rows
                    ]
                except Exception as e:
                    report_data['sections']['materials'] = []
            
            # Faktury (placeholder - závisí na struktuře DB)
            if 'invoices' in detail_sections:
                report_data['sections']['invoices'] = {'info': 'Modul faktur není aktivní - data nejsou k dispozici'}
            
            # Status plateb (placeholder)
            if 'payments' in detail_sections:
                report_data['sections']['payments'] = {'info': 'Modul plateb není aktivní - data nejsou k dispozici'}
            
            # Detail výdajů (placeholder)
            if 'expenses' in detail_sections:
                report_data['sections']['expenses'] = {'info': 'Modul výdajů není aktivní - data nejsou k dispozici'}
            
            # Subdodavatelé (placeholder)
            if 'subcontractors' in detail_sections:
                report_data['sections']['subcontractors'] = {'info': 'Modul subdodavatelů není aktivní - data nejsou k dispozici'}
        
        # ============================================================
        # PROJECT REPORT - Report konkrétního projektu
        # ============================================================
        elif report_type == 'project' and project_id:
            
            # Základní info o projektu
            if 'summary' in content_sections:
                try:
                    job = db.execute('''
                        SELECT * FROM jobs WHERE id = ?
                    ''', (project_id,)).fetchone()
                    if job:
                        report_data['sections']['project_info'] = dict(job)
                except Exception as e:
                    pass
            
            # Timeline - všechny výkazy
            if 'timeline' in content_sections:
                try:
                    rows = db.execute('''
                        SELECT 
                            t.id, t.date, t.hours, t.activity, t.place,
                            e.name as employee
                        FROM timesheets t
                        LEFT JOIN employees e ON e.id = t.employee_id
                        WHERE t.job_id = ?
                        ORDER BY t.date DESC
                    ''', (project_id,)).fetchall()
                    report_data['sections']['timesheets'] = [dict(r) for r in rows]
                    
                    # Souhrn
                    total_hours = sum(r['hours'] for r in rows)
                    report_data['sections']['hours_total'] = round(total_hours, 1)
                except Exception as e:
                    report_data['sections']['timesheets'] = []
            
            # Náklady na projekt
            if 'budget' in content_sections:
                try:
                    result = db.execute('''
                        SELECT 
                            COALESCE(SUM(t.hours), 0) as total_hours,
                            COALESCE(SUM(t.hours * COALESCE(e.hourly_rate, 200)), 0) as labor_cost
                        FROM timesheets t
                        LEFT JOIN employees e ON e.id = t.employee_id
                        WHERE t.job_id = ?
                    ''', (project_id,)).fetchone()
                    
                    report_data['sections']['costs'] = {
                        'total_hours': round(result['total_hours'] or 0, 1),
                        'labor_cost': round(result['labor_cost'] or 0, 0)
                    }
                except Exception as e:
                    report_data['sections']['costs'] = {}
            
            # Tým na projektu
            if 'team' in content_sections:
                try:
                    rows = db.execute('''
                        SELECT 
                            e.id, e.name, e.role,
                            SUM(t.hours) as hours,
                            COUNT(DISTINCT t.date) as days
                        FROM timesheets t
                        JOIN employees e ON e.id = t.employee_id
                        WHERE t.job_id = ?
                        GROUP BY e.id
                        ORDER BY hours DESC
                    ''', (project_id,)).fetchall()
                    report_data['sections']['team'] = [
                        {'id': r['id'], 'name': r['name'], 'role': r['role'] or '-',
                         'hours': round(r['hours'], 1), 'days': r['days']}
                        for r in rows
                    ]
                except Exception as e:
                    report_data['sections']['team'] = []
            
            # Úkoly projektu
            if 'tasks' in detail_sections:
                try:
                    rows = db.execute('''
                        SELECT 
                            t.id, t.title, t.status, t.due_date, t.description,
                            e.name as assignee
                        FROM tasks t
                        LEFT JOIN employees e ON e.id = t.employee_id
                        WHERE t.job_id = ?
                        ORDER BY 
                            CASE t.status 
                                WHEN 'open' THEN 1 
                                WHEN 'in_progress' THEN 2 
                                ELSE 3 
                            END,
                            t.id DESC
                    ''', (project_id,)).fetchall()
                    report_data['sections']['tasks'] = [dict(r) for r in rows]
                except Exception as e:
                    report_data['sections']['tasks'] = []
            
            # Materiály použité
            if 'materials' in detail_sections:
                try:
                    rows = db.execute('''
                        SELECT id, name, qty, unit
                        FROM job_materials
                        WHERE job_id = ?
                    ''', (project_id,)).fetchall()
                    report_data['sections']['materials'] = [dict(r) for r in rows]
                except Exception as e:
                    report_data['sections']['materials'] = []
            
            # Issues/problémy
            if 'risks' in content_sections:
                try:
                    rows = db.execute('''
                        SELECT 
                            i.id, i.title, i.status, i.severity, i.type, i.description,
                            e.name as assigned_to
                        FROM issues i
                        LEFT JOIN employees e ON e.id = i.assigned_to
                        WHERE i.job_id = ?
                        ORDER BY i.created_at DESC
                    ''', (project_id,)).fetchall()
                    report_data['sections']['issues'] = [dict(r) for r in rows]
                except Exception as e:
                    report_data['sections']['issues'] = []
        
        # ============================================================
        # CUSTOM REPORT - Vlastní kombinace
        # ============================================================
        elif report_type == 'custom':
            
            # Hodiny celkem
            if 'hours' in content_sections:
                try:
                    result = db.execute('''
                        SELECT COALESCE(SUM(hours), 0) as total
                        FROM timesheets
                        WHERE date BETWEEN ? AND ?
                    ''', (date_from, date_to)).fetchone()
                    report_data['sections']['hours'] = {'total': round(result['total'] or 0, 1)}
                except Exception as e:
                    report_data['sections']['hours'] = {'total': 0}
            
            # Úkoly
            if 'tasks' in content_sections:
                try:
                    rows = db.execute('''
                        SELECT status, COUNT(*) as count
                        FROM tasks
                        GROUP BY status
                    ''').fetchall()
                    total = sum(r['count'] for r in rows)
                    report_data['sections']['tasks'] = {
                        'total': total,
                        'by_status': [dict(r) for r in rows]
                    }
                except Exception as e:
                    report_data['sections']['tasks'] = {'total': 0, 'by_status': []}
            
            # Projekty
            if 'projects' in content_sections:
                try:
                    rows = db.execute('''
                        SELECT status, COUNT(*) as count
                        FROM jobs
                        GROUP BY status
                    ''').fetchall()
                    total = sum(r['count'] for r in rows)
                    report_data['sections']['projects'] = {
                        'total': total,
                        'by_status': [dict(r) for r in rows]
                    }
                except Exception as e:
                    report_data['sections']['projects'] = {'total': 0, 'by_status': []}
            
            # Tým
            if 'team' in content_sections:
                try:
                    result = db.execute('''
                        SELECT 
                            COUNT(*) as total,
                            SUM(CASE WHEN active = 1 THEN 1 ELSE 0 END) as active
                        FROM employees
                    ''').fetchone()
                    report_data['sections']['team'] = {
                        'total': result['total'] or 0,
                        'active': result['active'] or 0
                    }
                except Exception as e:
                    report_data['sections']['team'] = {'total': 0, 'active': 0}
            
            # Sklad
            if 'warehouse' in content_sections:
                try:
                    result = db.execute('''
                        SELECT 
                            COUNT(*) as items,
                            COALESCE(SUM(quantity * COALESCE(unit_price, 0)), 0) as value
                        FROM warehouse_items
                    ''').fetchone()
                    report_data['sections']['warehouse'] = {
                        'items': result['items'] or 0,
                        'value': round(result['value'] or 0, 0)
                    }
                except Exception as e:
                    report_data['sections']['warehouse'] = {'items': 0, 'value': 0}
            
            # Školka
            if 'nursery' in content_sections:
                try:
                    result = db.execute('''
                        SELECT 
                            COUNT(*) as total_plants,
                            COALESCE(SUM(quantity), 0) as total_quantity
                        FROM nursery_plants
                    ''').fetchone()
                    report_data['sections']['nursery'] = {
                        'total_plants': result['total_plants'] or 0,
                        'total_quantity': result['total_quantity'] or 0
                    }
                except Exception as e:
                    report_data['sections']['nursery'] = {'total_plants': 0, 'total_quantity': 0}
        
        # Přidat souhrn
        report_data['summary'] = {
            'sections_count': len(report_data['sections']),
            'has_data': any(report_data['sections'].values())
        }
        
        return jsonify(report_data)
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@reports_bp.route('/api/reports/projects')
def api_reports_projects():
    """Get list of projects for report selector"""
    u, err = require_role()
    if err: return err
    
    db = get_db()
    jobs = db.execute('''
        SELECT id, COALESCE(name, title, 'Projekt ' || id) as name, status, client, city
        FROM jobs
        ORDER BY id DESC
    ''').fetchall()
    return jsonify([dict(r) for r in jobs])

@reports_bp.route('/api/reports/employees')
def api_reports_employees():
    """Get list of employees for report selector"""
    u, err = require_role()
    if err: return err
    
    db = get_db()
    # Zjisti jestli existuje sloupec active
    cols = {r[1] for r in db.execute("PRAGMA table_info(employees)").fetchall()}
    
    if 'active' in cols:
        employees = db.execute('''
            SELECT id, name, role, active
            FROM employees
            WHERE active = 1
            ORDER BY name
        ''').fetchall()
    else:
        employees = db.execute('''
            SELECT id, name, role, 1 as active
            FROM employees
            ORDER BY name
        ''').fetchall()
    return jsonify([dict(r) for r in employees])

print("✅ Reports API loaded")

print("✅ Velitelský Panel loaded")

# ================================================================
# PLANNING EXTENDED ROUTES - All New Features
# ================================================================
import planning_extended_api as ext_api
ext_api.get_db = get_db

# Nursery - Trvalkové školka 🌸
@reports_bp.route('/api/plant-catalog/search', methods=['GET'])
def api_plant_catalog_search():
    """Vyhledávání v katalogu rostlin (autocomplete)"""
    u, err = require_auth()
    if err: return err
    
    query = request.args.get('q', '').strip()
    limit = request.args.get('limit', 20, type=int)
    
    if not query or len(query) < 2:
        return jsonify({
            'success': False,
            'message': 'Zadej alespoň 2 znaky pro vyhledávání'
        }), 400
    
    try:
        db = get_db()
        
        # Pokus o FTS, pokud není dostupné, použij LIKE
        try:
            results = db.execute('''
                SELECT pc.id, pc.latin_name, pc.variety, pc.container_size,
                       pc.flower_color, pc.flowering_time, pc.height,
                       pc.light_requirements, pc.hardiness_zone
                FROM plant_catalog_fts fts
                JOIN plant_catalog pc ON pc.id = fts.rowid
                WHERE plant_catalog_fts MATCH ?
                ORDER BY rank
                LIMIT ?
            ''', (f'{query}*', limit)).fetchall()
        except Exception as fts_error:
            # FTS není dostupné, použij LIKE fallback
            print(f"[INFO] FTS not available, using LIKE: {fts_error}")
            search_pattern = f'%{query}%'
            results = db.execute('''
                SELECT id, latin_name, variety, container_size,
                       flower_color, flowering_time, height,
                       light_requirements, hardiness_zone
                FROM plant_catalog
                WHERE latin_name LIKE ? OR variety LIKE ? OR notes LIKE ?
                ORDER BY latin_name
                LIMIT ?
            ''', (search_pattern, search_pattern, search_pattern, limit)).fetchall()
        
        plants = []
        for row in results:
            full_name = row['latin_name']
            if row['variety']:
                full_name += f" '{row['variety']}'"
            if row['container_size']:
                full_name += f" - {row['container_size']}"
            
            plants.append({
                'id': row['id'],
                'full_name': full_name,
                'latin_name': row['latin_name'],
                'variety': row['variety'],
                'container_size': row['container_size'],
                'flower_color': row['flower_color'],
                'flowering_time': row['flowering_time'],
                'height': row['height'],
                'light_requirements': row['light_requirements'],
                'hardiness_zone': row['hardiness_zone']
            })
        
        return jsonify({
            'success': True,
            'plants': plants,
            'count': len(plants)
        })
        
    except Exception as e:
        print(f"[ERROR] plant_catalog_search: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'message': f'Chyba při vyhledávání: {str(e)}'
        }), 500

# Additional routes from main.py
@reports_bp.route('/reports-hub')
def reports_hub_page():
    return send_from_directory('.', 'reports-hub.html')

@reports_bp.route('/reports-daily')
def reports_daily_page():
    return send_from_directory('.', 'reports-daily.html')

@reports_bp.route('/reports-week')
def reports_week_page():
    return send_from_directory('.', 'reports-week.html')

@reports_bp.route('/reports-project')
def reports_project_page():
    return send_from_directory('.', 'reports-project.html')

# ================================================================
# REPORTS GENERATOR API - KOMPLETNÍ FUNKČNÍ VERZE
# ================================================================

def api_get_task_photos(task_id):
    return ext_api.get_task_photos(task_id)

# Plant database 🌺
