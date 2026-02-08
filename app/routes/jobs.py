# Green David App
from flask import Blueprint, jsonify, request, render_template, send_from_directory
from datetime import datetime, timedelta
import json
from app.database import get_db
from app.utils.permissions import require_auth, require_role, requires_role
from app.utils.helpers import (
    audit_event, _normalize_date,
    _jobs_info, _job_title_col, _job_select_all, 
    _job_insert_cols_and_vals, _job_title_update_set
)
from assignment_helpers import get_task_assignees

jobs_bp = Blueprint('jobs', __name__)


@jobs_bp.route("/archive")
def view_archive():
    from flask import render_template
    u, err = require_auth()
    if err:
        return err
    db = get_db()
    rows = [dict(r) for r in db.execute(
        "SELECT id,title,client,city,code,status,date,completed_at "
        "FROM jobs "
        "WHERE lower(status) LIKE 'dokon%' "
        "ORDER BY COALESCE(date(completed_at), date(date)) DESC"
    ).fetchall()]
    months = {}
    for r in rows:
        src = r.get("completed_at") or r.get("date") or ""
        ym = ""
        try:
            # normalize to YYYY-MM
            if src and len(src) >= 7:
                ym = f"{src[0:4]}-{src[5:7]}"
        except Exception:
            ym = ""
        months.setdefault(ym or "unknown", []).append(r)
    # group by year for template
    by_year = {}
    for ym, items in months.items():
        y = (ym or "unknown").split("-")[0]
        by_year.setdefault(y, []).append((ym, items))
    # sort
    for y in by_year:
        by_year[y].sort(key=lambda x: x[0], reverse=True)
    years = sorted(by_year.items(), key=lambda x: x[0], reverse=True)
    return render_template("archive.html", me=u, years=years)


@jobs_bp.route("/api/jobs/archive")
def api_jobs_archive():
    u, err = require_auth()
    if err: 
        return err
    db = get_db()
    rows = [dict(r) for r in db.execute("SELECT id,title,client,city,code,status,date,completed_at FROM jobs WHERE lower(status) LIKE 'dokon%' ORDER BY COALESCE(date(completed_at), date(date)) DESC").fetchall()]
    months = {}
    for r in rows:
        # prefer completed_at month, fallback to scheduled date
        src = r.get("completed_at") or r.get("date") or ""
        ym = ""
        try:
            # normalize to YYYY-MM
            if src and len(src)>=7:
                ym = f"{src[0:4]}-{src[5:7]}"
        except Exception:
            ym = ""
        months.setdefault(ym or "unknown", []).append(r)
    return jsonify({"ok": True, "months": months})


@jobs_bp.route("/jobs.html")
def jobs_html():
    return send_from_directory(".", "jobs.html")


@jobs_bp.route("/jobs/<int:job_id>")
def job_detail_page(job_id):
    return send_from_directory(".", "job.html")


# Additional jobs routes from main.py
@jobs_bp.route("/api/jobs", methods=["GET","POST","PATCH","DELETE"])
def api_jobs():
    db = get_db()
    if request.method == "GET":
        rows = [dict(r) for r in db.execute(_job_select_all() + " ORDER BY date(date) DESC, id DESC").fetchall()]
        for r in rows:
            if "date" in r and r["date"]:
                r["date"] = _normalize_date(r["date"])
        # hide completed jobs from main list (they are visible only in archive)
        visible = []
        for r in rows:
            status = (r.get("status") or "").strip().lower()
            if status.startswith("dokon"):  # "Dokončeno"
                continue
            visible.append(r)
        return jsonify({"ok": True, "jobs": visible})

    # write operations require manager/admin
    u, err = require_role(write=True)
    if err: return err

    data = request.get_json(force=True, silent=True) or {}
    title = (data.get("title") or "").strip()
    client = (data.get("client") or "").strip()
    status = (data.get("status") or "Plán").strip()
    city   = (data.get("city")   or "").strip()
    code   = (data.get("code")   or "").strip()
    note   = data.get("note") or ""
    dt     = _normalize_date(data.get("date"))

    if request.method == "POST":
        try:
            req = [title, city, code, dt]
            if not all((v is not None and str(v).strip()!='') for v in req):
                return jsonify({"ok": False, "error":"missing_fields"}), 400
            cols, vals = _job_insert_cols_and_vals(title, client, status, city, code, dt, note, owner_id=u["id"])
            sql = "INSERT INTO jobs(" + ",".join(cols) + ") VALUES (" + ",".join(["?"]*len(vals)) + ")"
            cur = db.execute(sql, vals)
            job_id = cur.lastrowid
            db.commit()
            audit_event(u.get("id"), "create", "job", job_id, after={"title": title, "client": client, "status": status, "city": city, "code": code, "date": dt})
            print(f"✓ Job '{title}' created successfully")
            return jsonify({"ok": True})
        except Exception as e:
            db.rollback()
            print(f"✗ Error creating job: {e}")
            return jsonify({"ok": False, "error": str(e)}), 500

    if request.method == "PATCH":
        try:
            jid = data.get("id")
            if not jid: return jsonify({"ok": False, "error":"missing_id"}), 400
            updates = []; params = []
            if "title" in data and data["title"] is not None:
                updates += _job_title_update_set(params, data["title"])
            for f in ("client","status","city","code","date","note","created_date","start_date","progress","deadline","address","location","estimated_value","budget"):
                if f in data:
                    if f in ("date", "created_date", "start_date", "deadline"):
                        # Normalizuj datum - pokud je prázdné/null, uloží se jako NULL do DB
                        if data[f]:
                            v = _normalize_date(data[f])
                        else:
                            v = None  # Explicitně None pro NULL v DB
                    elif f=="progress":
                        v = int(data[f]) if data[f] is not None else 0
                    else:
                        v = data[f] if data[f] is not None else ""
                    # Přidej do updates i když je hodnota None (pro NULL v DB)
                    updates.append(f"{f}=?"); params.append(v)
                    print(f"[PATCH] Updating {f} = {v} (type: {type(v).__name__})")
            # Touch legacy updated_at if present
            info = _jobs_info()
            if "updated_at" in info:
                updates.append("updated_at=?"); params.append(datetime.utcnow().isoformat())
            # Optional owner change if present
            if "owner_id" in info and data.get("owner_id") is not None:
                updates.append("owner_id=?"); params.append(int(data.get("owner_id")))
            if not updates: return jsonify({"ok": False, "error":"nothing_to_update"}), 400
            params.append(int(jid))
            db.execute("UPDATE jobs SET " + ", ".join(updates) + " WHERE id=?", params)
            db.commit()
            # if status is Dokončeno, ensure completed_at is set
            try:
                job = db.execute("SELECT id,status,completed_at FROM jobs WHERE id=?", (jid,)).fetchone()
                if job:
                    s = (job["status"] or "").lower()
                    if s.startswith("dokon"):
                        if not job["completed_at"]:
                            today = datetime.utcnow().strftime("%Y-%m-%d")
                            db.execute("UPDATE jobs SET completed_at=? WHERE id=?", (today, jid))
                            db.commit()
            except Exception:
                pass
            print(f"✓ Job {jid} updated successfully")
            return jsonify({"ok": True})
        except Exception as e:
            db.rollback()
            print(f"✗ Error updating job: {e}")
            return jsonify({"ok": False, "error": str(e)}), 500

    # DELETE
    try:
        jid = request.args.get("id", type=int)
        if not jid: return jsonify({"ok": False, "error":"missing_id"}), 400
        # audit snapshot
        before = db.execute("SELECT id, COALESCE(title,name,'') as title, client, status, city, code, date, note FROM jobs WHERE id=?", (jid,)).fetchone()
        before = dict(before) if before else None
        db.execute("DELETE FROM jobs WHERE id=?", (jid,))
        db.commit()
        audit_event(u.get("id"), "delete", "job", jid, before=before)
        print(f"✓ Job {jid} deleted successfully")
        return jsonify({"ok": True})
    except Exception as e:
        db.rollback()
        print(f"✗ Error deleting job: {e}")
        return jsonify({"ok": False, "error": str(e)}), 500


# -------- Job detail & materials/tools/assignments --------
@jobs_bp.route("/api/jobs/<int:job_id>", methods=["GET"])
def api_job_detail(job_id):
    u, err = require_role(write=False)
    if err: return err
    db = get_db()
    title_col = _job_title_col()
    
    # Get job with all available columns
    cols = [r[1] for r in db.execute("PRAGMA table_info(jobs)").fetchall()]
    select_cols = ["id", title_col + " AS title", "client", "status", "city", "code", "date", "note"]
    optional_cols = ["budget", "cost_spent", "labor_cost_total", "time_spent_minutes", "hourly_rate", 
                     "budget_remaining", "margin", "time_planned_minutes"]
    for col in optional_cols:
        if col in cols:
            select_cols.append(col)
    
    job = db.execute(f"SELECT {', '.join(select_cols)} FROM jobs WHERE id=?", (job_id,)).fetchone()
    if not job: return jsonify({"ok": False, "error": "not_found"}), 404
    job = dict(job)
    if job.get("date"): job["date"] = _normalize_date(job["date"])
    
    # Calculate finance summary
    budget = float(job.get("budget") or 0)
    cost_spent = float(job.get("cost_spent") or job.get("labor_cost_total") or 0)
    budget_remaining = budget - cost_spent if budget > 0 else None
    margin_pct = ((budget - cost_spent) / budget * 100) if budget > 0 else None
    
    # Get worklogs summary for cost burn rate
    worklogs_summary = db.execute("""
        SELECT 
            COUNT(*) as count,
            SUM(COALESCE(duration_minutes, CAST(hours * 60 AS INTEGER))) as total_minutes,
            SUM(COALESCE(labor_cost, 0)) as total_cost,
            MIN(date) as first_date,
            MAX(date) as last_date
        FROM timesheets
        WHERE job_id = ?
    """, (job_id,)).fetchone()
    
    finance_summary = {
        "budget": budget,
        "cost_spent": cost_spent,
        "budget_remaining": budget_remaining,
        "margin_pct": margin_pct,
        "worklogs_count": worklogs_summary["count"] or 0,
        "total_hours": round((worklogs_summary["total_minutes"] or 0) / 60, 1),
        "total_cost": float(worklogs_summary["total_cost"] or 0),
        "first_date": worklogs_summary["first_date"],
        "last_date": worklogs_summary["last_date"]
    }
    
    # Get material consumption from worklogs
    material_consumption = []
    missing_materials = []
    try:
        worklog_rows = db.execute("""
            SELECT material_used
            FROM timesheets
            WHERE job_id = ? AND material_used IS NOT NULL AND material_used != ''
        """, (job_id,)).fetchall()
        
        # Aggregate material consumption
        consumption_map = {}
        for row in worklog_rows:
            try:
                import json
                materials = json.loads(row['material_used']) if isinstance(row['material_used'], str) else row['material_used']
                if isinstance(materials, list):
                    for mat in materials:
                        item_id = mat.get('item_id')
                        qty = float(mat.get('qty', 0))
                        unit = mat.get('unit', 'ks')
                        name = mat.get('name', '')
                        
                        if item_id:
                            key = str(item_id)
                            if key not in consumption_map:
                                consumption_map[key] = {'item_id': item_id, 'qty': 0, 'unit': unit, 'name': name}
                            consumption_map[key]['qty'] += qty
                        elif name:
                            key = name.lower()
                            if key not in consumption_map:
                                consumption_map[key] = {'item_id': None, 'qty': 0, 'unit': unit, 'name': name}
                            consumption_map[key]['qty'] += qty
            except Exception as e:
                print(f"[MATERIAL] Error parsing material_used: {e}")
                pass
        
        # Get warehouse items info for consumed materials
        for key, cons in consumption_map.items():
            item_id = cons.get('item_id')
            if item_id:
                try:
                    wi = db.execute("SELECT name, quantity, min_quantity, unit FROM warehouse_items WHERE id=?", (item_id,)).fetchone()
                    if wi:
                        cons['name'] = wi['name']
                        cons['stock_qty'] = wi['quantity'] or 0
                        cons['min_qty'] = wi['min_quantity'] or 0
                        cons['unit'] = wi['unit'] or cons['unit']
                        
                        # Check if material is missing
                        if cons['stock_qty'] < cons['qty']:
                            missing_materials.append({
                                'name': cons['name'],
                                'consumed': cons['qty'],
                                'available': cons['stock_qty'],
                                'unit': cons['unit']
                            })
                except:
                    pass
            
            material_consumption.append(cons)
    except Exception as e:
        print(f"[MATERIAL] Error getting material consumption: {e}")
        pass
    
    mats = [dict(r) for r in db.execute("SELECT id, name, qty, unit FROM job_materials WHERE job_id=? ORDER BY id ASC", (job_id,)).fetchall()]
    tools = [dict(r) for r in db.execute("SELECT id, name, qty, unit FROM job_tools WHERE job_id=? ORDER BY id ASC", (job_id,)).fetchall()]
    assigns = [r["employee_id"] for r in db.execute("SELECT employee_id FROM job_assignments WHERE job_id=? ORDER BY employee_id ASC", (job_id,)).fetchall()]
    
    return jsonify({
        "ok": True, 
        "job": job, 
        "materials": mats, 
        "tools": tools, 
        "assignments": assigns, 
        "finance": finance_summary,
        "material_consumption": material_consumption,
        "missing_materials": missing_materials
    })


# ============================================================================
# JOBS 2.0 - Enhanced Jobs API with Metrics (Zakázky jako mikro-vesmír)
# ============================================================================

@jobs_bp.route("/api/jobs/overview")
def api_jobs_metrics_overview():
    """Get all jobs with calculated metrics for Kanban/List/Timeline views"""
    u, err = require_role(write=False)
    if err: return err
    
    db = get_db()
    info = _jobs_info()
    
    # Dynamicky sestavit SELECT podle dostupných sloupců
    base_cols = ["id", "client", "status", "city", "code", "date", "note"]
    optional_cols = ["created_date", "start_date", "deadline", "address", "progress", 
                     "budget", "estimated_value", "actual_value", "budget_labor", 
                     "budget_materials", "budget_equipment", "budget_other",
                     "actual_labor_cost", "actual_material_cost", "profit_margin",
                     "budget_spent_percent", "completion_percent", "weather_dependent",
                     "priority", "hourly_rate", "estimated_hours", "actual_hours"]
    
    select_cols = base_cols.copy()
    for col in optional_cols:
        if col in info:
            select_cols.append(col)
    
    # Title/name handling
    title_col = _job_title_col()
    if title_col == "name":
        select_cols.insert(0, "name AS title")
    else:
        select_cols.insert(0, "title")
    
    sql = f"SELECT {', '.join(select_cols)} FROM jobs ORDER BY date(date) DESC, id DESC"
    rows = db.execute(sql).fetchall()
    
    jobs_with_metrics = []
    today = datetime.now().date()
    
    # Pre-fetch všechny potřebné data najednou pro efektivitu
    # 1. Materiály pro všechny zakázky
    all_materials = {}
    try:
        mat_rows = db.execute("""
            SELECT jm.job_id, jm.name, jm.qty, jm.unit, jm.status,
                   wi.quantity as stock_qty, wi.min_quantity
            FROM job_materials jm
            LEFT JOIN warehouse_items wi ON wi.name = jm.name
        """).fetchall()
        for m in mat_rows:
            jid = m['job_id']
            if jid not in all_materials:
                all_materials[jid] = []
            all_materials[jid].append(dict(m))
    except:
        pass
    
    # 2. Assignments pro všechny zakázky
    all_assignments = {}
    try:
        assign_rows = db.execute("""
            SELECT ja.job_id, ja.employee_id, e.name, e.role
            FROM job_assignments ja
            JOIN employees e ON e.id = ja.employee_id
        """).fetchall()
        for a in assign_rows:
            jid = a['job_id']
            if jid not in all_assignments:
                all_assignments[jid] = []
            all_assignments[jid].append({
                'employee_id': a['employee_id'],
                'name': a['name'],
                'role': a['role']
            })
    except:
        pass
    
    # 3. Timesheets - hodiny za posledních 7 dní per zaměstnanec
    week_ago = (today - timedelta(days=7)).isoformat()
    employee_hours_week = {}
    try:
        ts_rows = db.execute("""
            SELECT employee_id, SUM(hours) as total_hours
            FROM timesheets
            WHERE date >= ?
            GROUP BY employee_id
        """, (week_ago,)).fetchall()
        for ts in ts_rows:
            employee_hours_week[ts['employee_id']] = ts['total_hours'] or 0
    except:
        pass
    
    # 4. Timesheets per job (celkové hodiny)
    job_hours = {}
    try:
        jh_rows = db.execute("""
            SELECT job_id, SUM(hours) as total_hours, COUNT(DISTINCT employee_id) as workers
            FROM timesheets
            GROUP BY job_id
        """).fetchall()
        for jh in jh_rows:
            job_hours[jh['job_id']] = {
                'total_hours': jh['total_hours'] or 0,
                'workers': jh['workers'] or 0
            }
    except:
        pass
    
    # 5. Tasks per job
    job_tasks = {}
    try:
        task_rows = db.execute("""
            SELECT job_id, 
                   COUNT(*) as total,
                   SUM(CASE WHEN status IN ('done','completed','Dokončeno') THEN 1 ELSE 0 END) as completed,
                   SUM(CASE WHEN due_date < date('now') AND status NOT IN ('done','completed','Dokončeno') THEN 1 ELSE 0 END) as overdue
            FROM tasks
            GROUP BY job_id
        """).fetchall()
        for t in task_rows:
            job_tasks[t['job_id']] = {
                'total': t['total'] or 0,
                'completed': t['completed'] or 0,
                'overdue': t['overdue'] or 0
            }
    except:
        pass
    
    for row in rows:
        job = dict(row)
        job_id = job['id']
        
        # Normalize date
        if job.get('date'):
            job['date'] = _normalize_date(job['date'])
        
        # Skip completed jobs (they go to archive)
        status = (job.get('status') or '').strip().lower()
        if status.startswith('dokon'):
            continue
        
        # === Calculate Metrics ===
        
        # Time progress
        time_progress = 0
        start_date = job.get('start_date') or job.get('created_date')
        deadline = job.get('deadline') or job.get('date')
        days_until = None
        
        if deadline:
            try:
                deadline_dt = datetime.strptime(deadline[:10], '%Y-%m-%d').date()
                days_until = (deadline_dt - today).days
                
                if start_date:
                    start_dt = datetime.strptime(start_date[:10], '%Y-%m-%d').date()
                    total_days = max(1, (deadline_dt - start_dt).days)
                    elapsed_days = (today - start_dt).days
                    time_progress = min(100, max(0, (elapsed_days / total_days) * 100))
            except:
                pass
        
        # Budget calculations
        budget = job.get('budget') or job.get('estimated_value') or 0
        if not budget:
            # Spočítej z breakdown
            budget = (job.get('budget_labor') or 0) + (job.get('budget_materials') or 0) + \
                     (job.get('budget_equipment') or 0) + (job.get('budget_other') or 0)
        
        actual_cost = (job.get('actual_labor_cost') or 0) + (job.get('actual_material_cost') or 0)
        if not actual_cost and job.get('actual_value'):
            actual_cost = job.get('actual_value')
        
        budget_progress = (actual_cost / budget * 100) if budget > 0 else 0
        if job.get('budget_spent_percent'):
            budget_progress = job.get('budget_spent_percent')
        
        # Margin
        margin_pct = job.get('profit_margin')
        if margin_pct is None and budget > 0:
            margin_pct = ((budget - actual_cost) / budget) * 100
        margin_pct = margin_pct or 50  # default
        
        # Material status
        materials = all_materials.get(job_id, [])
        material_status = 'ok'
        missing_items = []
        for mat in materials:
            mat_status = mat.get('status', '').lower()
            stock_qty = mat.get('stock_qty') or 0
            needed_qty = mat.get('qty') or 0
            
            if mat_status in ('missing', 'chybí') or stock_qty < needed_qty:
                material_status = 'missing'
                missing_items.append({'name': mat['name'], 'needed': needed_qty, 'available': stock_qty})
            elif mat_status not in ('ok', 'reserved', 'rezervováno') and material_status != 'missing':
                material_status = 'partial'
        
        # Team & overload
        assigned = all_assignments.get(job_id, [])
        overloaded = []
        for emp in assigned:
            emp_hours = employee_hours_week.get(emp['employee_id'], 0)
            if emp_hours > 45:
                overloaded.append({
                    'employee_id': emp['employee_id'],
                    'name': emp['name'],
                    'hours_week': round(emp_hours, 1)
                })
        
        team_utilization = 0
        if assigned:
            total_team_hours = sum(employee_hours_week.get(e['employee_id'], 0) for e in assigned)
            max_hours = len(assigned) * 40  # 40h týdně standard
            team_utilization = min(100, (total_team_hours / max_hours * 100)) if max_hours > 0 else 0
        
        # Job hours from timesheets
        jh = job_hours.get(job_id, {'total_hours': 0, 'workers': 0})
        
        # Tasks
        jt = job_tasks.get(job_id, {'total': 0, 'completed': 0, 'overdue': 0})
        
        # Weather risk (simplified - based on weather_dependent flag)
        weather_dependent = job.get('weather_dependent', False)
        weather_risk = 'none'
        if weather_dependent:
            if days_until is not None and days_until <= 7:
                weather_risk = 'high'
            elif days_until is not None and days_until <= 14:
                weather_risk = 'medium'
            else:
                weather_risk = 'low'
        
        # === Risk Score (0-100) ===
        risk_score = 0
        alerts = []
        
        # Deadline risk
        if days_until is not None:
            completion = job.get('completion_percent') or job.get('progress') or 0
            if days_until < 0:
                risk_score += 40
                alerts.append({'type': 'overdue', 'severity': 'high', 'text': f'Po termínu {abs(days_until)} dní', 'icon': '⏰'})
            elif days_until <= 7 and completion < 80:
                risk_score += 30
                alerts.append({'type': 'deadline', 'severity': 'medium', 'text': f'Deadline za {days_until} dní', 'icon': '⚠️'})
            elif days_until <= 3:
                risk_score += 20
        
        # Budget risk
        if budget_progress > 100:
            risk_score += 25
            alerts.append({'type': 'budget', 'severity': 'high', 'text': f'Rozpočet překročen o {round(budget_progress-100)}%', 'icon': '💸'})
        elif budget_progress > 80 and (job.get('completion_percent') or 0) < 80:
            risk_score += 15
            alerts.append({'type': 'budget', 'severity': 'medium', 'text': 'Rozpočet téměř vyčerpán', 'icon': '💰'})
        
        # Material risk
        if material_status == 'missing':
            risk_score += 20
            alerts.append({'type': 'material', 'severity': 'medium', 'text': f'{len(missing_items)} položek chybí', 'icon': '📦'})
        
        # Team overload risk
        if overloaded:
            risk_score += 15
            alerts.append({'type': 'overload', 'severity': 'medium', 'text': f'{len(overloaded)} přetížených', 'icon': '👥'})
        
        # Weather risk
        if weather_risk == 'high':
            risk_score += 15
            alerts.append({'type': 'weather', 'severity': 'medium', 'text': 'Počasí ohrožuje termín', 'icon': '🌧️'})
        
        # Tasks overdue
        if jt['overdue'] > 0:
            risk_score += 10
            alerts.append({'type': 'tasks', 'severity': 'low', 'text': f'{jt["overdue"]} úkolů po termínu', 'icon': '📋'})
        
        risk_score = min(100, risk_score)
        
        # AI Score (inverse of risk, with bonus for good metrics)
        ai_score = max(0, 100 - risk_score)
        if margin_pct > 30:
            ai_score = min(100, ai_score + 5)
        if material_status == 'ok':
            ai_score = min(100, ai_score + 5)
        
        # Ghost plan suggestion (AI recommendation for timeline)
        ghost_plan = None
        if risk_score > 50 and days_until is not None and days_until > 0:
            suggested_delay = 2 if risk_score < 70 else 5
            if overloaded:
                ghost_plan = {
                    'type': 'delay',
                    'days': suggested_delay,
                    'reason': 'Přetížení týmu',
                    'suggested_date': (datetime.strptime(deadline[:10], '%Y-%m-%d') + timedelta(days=suggested_delay)).strftime('%Y-%m-%d')
                }
            elif material_status == 'missing':
                ghost_plan = {
                    'type': 'delay',
                    'days': suggested_delay,
                    'reason': 'Chybějící materiál',
                    'suggested_date': (datetime.strptime(deadline[:10], '%Y-%m-%d') + timedelta(days=suggested_delay)).strftime('%Y-%m-%d')
                }
        
        # Build metrics object
        job['metrics'] = {
            'margin_pct': round(margin_pct, 1),
            'risk_pct': risk_score,
            'risk_level': 'high' if risk_score >= 50 else 'medium' if risk_score >= 25 else 'low',
            'ai_score': round(ai_score),
            'alerts': alerts,
            'time_progress_pct': round(time_progress, 1),
            'budget_progress_pct': round(budget_progress, 1),
            'days_until_deadline': days_until,
            'material': {
                'status': material_status,
                'missing_count': len(missing_items),
                'missing_items': missing_items[:5]  # Top 5
            },
            'team': {
                'assigned': assigned,
                'assigned_count': len(assigned),
                'overload': overloaded,
                'utilization_pct': round(team_utilization, 1)
            },
            'hours': {
                'total': round(jh['total_hours'], 1),
                'workers': jh['workers'],
                'estimated': job.get('estimated_hours') or 0
            },
            'tasks': jt,
            'weather': {
                'dependent': weather_dependent,
                'risk': weather_risk
            },
            'ghost_plan': ghost_plan
        }
        
        jobs_with_metrics.append(job)
    
    return jsonify({'ok': True, 'jobs': jobs_with_metrics})


@jobs_bp.route("/api/jobs/<int:job_id>/hub")
def api_job_hub(job_id):
    """Get detailed job hub with AI panel - mikro-vesmír zakázky"""
    u, err = require_role(write=False)
    if err: return err
    
    db = get_db()
    info = _jobs_info()
    
    # Načti základní data zakázky
    title_col = _job_title_col()
    job = db.execute(f"SELECT * FROM jobs WHERE id=?", (job_id,)).fetchone()
    if not job:
        return jsonify({'ok': False, 'error': 'not_found'}), 404
    
    job = dict(job)
    today = datetime.now().date()
    
    # === Materials ===
    materials = []
    try:
        mat_rows = db.execute("""
            SELECT jm.*, wi.quantity as stock_qty, wi.min_quantity, wi.unit_price
            FROM job_materials jm
            LEFT JOIN warehouse_items wi ON wi.name = jm.name
            WHERE jm.job_id = ?
        """, (job_id,)).fetchall()
        materials = [dict(m) for m in mat_rows]
    except:
        pass
    
    # === Team Assignments ===
    team = []
    try:
        team_rows = db.execute("""
            SELECT e.id, e.name, e.role, e.hourly_rate,
                   (SELECT SUM(hours) FROM timesheets WHERE employee_id = e.id AND date >= date('now', '-7 days')) as hours_week,
                   (SELECT SUM(hours) FROM timesheets WHERE employee_id = e.id AND job_id = ?) as hours_on_job
            FROM job_assignments ja
            JOIN employees e ON e.id = ja.employee_id
            WHERE ja.job_id = ?
        """, (job_id, job_id)).fetchall()
        team = [dict(t) for t in team_rows]
    except:
        pass
    
    # === Timesheets Summary ===
    timesheets_summary = {'total_hours': 0, 'total_cost': 0, 'entries': 0, 'by_employee': []}
    try:
        ts_rows = db.execute("""
            SELECT e.name, SUM(t.hours) as hours, COUNT(*) as entries
            FROM timesheets t
            JOIN employees e ON e.id = t.employee_id
            WHERE t.job_id = ?
            GROUP BY t.employee_id
            ORDER BY hours DESC
        """, (job_id,)).fetchall()
        
        total_hours = 0
        for ts in ts_rows:
            total_hours += ts['hours'] or 0
            timesheets_summary['by_employee'].append({
                'name': ts['name'],
                'hours': round(ts['hours'] or 0, 1),
                'entries': ts['entries']
            })
        timesheets_summary['total_hours'] = round(total_hours, 1)
        timesheets_summary['entries'] = sum(ts['entries'] for ts in ts_rows)
        
        # Estimate cost
        avg_rate = 200  # Default hourly rate
        timesheets_summary['total_cost'] = round(total_hours * avg_rate, 0)
    except:
        pass
    
    # === Finance Summary ===
    budget = job.get('budget') or job.get('estimated_value') or 0
    if not budget:
        budget = (job.get('budget_labor') or 0) + (job.get('budget_materials') or 0) + \
                 (job.get('budget_equipment') or 0) + (job.get('budget_other') or 0)
    
    actual_labor = timesheets_summary['total_cost']
    actual_materials = sum((m.get('qty') or 0) * (m.get('unit_price') or 0) for m in materials)
    actual_total = actual_labor + actual_materials
    
    finance_summary = {
        'budget': round(budget, 0),
        'budget_breakdown': {
            'labor': job.get('budget_labor') or 0,
            'materials': job.get('budget_materials') or 0,
            'equipment': job.get('budget_equipment') or 0,
            'other': job.get('budget_other') or 0
        },
        'actual': {
            'total': round(actual_total, 0),
            'labor': round(actual_labor, 0),
            'materials': round(actual_materials, 0)
        },
        'remaining': round(budget - actual_total, 0),
        'spent_pct': round((actual_total / budget * 100) if budget > 0 else 0, 1),
        'margin_pct': round(((budget - actual_total) / budget * 100) if budget > 0 else 0, 1)
    }
    
    # === Tasks Summary ===
    tasks_summary = {'total': 0, 'completed': 0, 'in_progress': 0, 'overdue': 0, 'items': []}
    try:
        task_rows = db.execute("""
            SELECT t.id, t.title, t.status, t.due_date, e.name as assignee
            FROM tasks t
            LEFT JOIN employees e ON e.id = t.employee_id
            WHERE t.job_id = ?
            ORDER BY t.due_date ASC
        """, (job_id,)).fetchall()
        
        for task in task_rows:
            tasks_summary['total'] += 1
            status = (task['status'] or '').lower()
            if status in ('done', 'completed', 'dokončeno'):
                tasks_summary['completed'] += 1
            elif status in ('in_progress', 'v práci'):
                tasks_summary['in_progress'] += 1
            
            if task['due_date']:
                try:
                    due = datetime.strptime(task['due_date'][:10], '%Y-%m-%d').date()
                    if due < today and status not in ('done', 'completed', 'dokončeno'):
                        tasks_summary['overdue'] += 1
                except:
                    pass
            
            tasks_summary['items'].append(dict(task))
    except:
        pass
    
    # === AI Panel (Doporučení) ===
    ai_panel = {
        'risk_deadline': 0,
        'risk_deadline_text': '',
        'material_missing': [],
        'team_overload': [],
        'recommendations': []
    }
    
    # Deadline risk
    deadline = job.get('deadline') or job.get('date')
    completion = job.get('completion_percent') or job.get('progress') or 0
    if deadline:
        try:
            deadline_dt = datetime.strptime(deadline[:10], '%Y-%m-%d').date()
            days_until = (deadline_dt - today).days
            
            if days_until < 0:
                ai_panel['risk_deadline'] = 100
                ai_panel['risk_deadline_text'] = f'Zakázka je {abs(days_until)} dní po termínu!'
                ai_panel['recommendations'].append({
                    'type': 'urgent',
                    'icon': '🚨',
                    'text': 'Okamžitě kontaktovat klienta a domluvit nový termín'
                })
            elif days_until <= 7 and completion < 80:
                ai_panel['risk_deadline'] = 70
                ai_panel['risk_deadline_text'] = f'Zbývá {days_until} dní, dokončeno pouze {completion}%'
                ai_panel['recommendations'].append({
                    'type': 'warning',
                    'icon': '⚠️',
                    'text': 'Zvážit posílení týmu nebo přesčasy'
                })
            elif days_until <= 14:
                ai_panel['risk_deadline'] = 30
                ai_panel['risk_deadline_text'] = f'Zbývá {days_until} dní'
            else:
                ai_panel['risk_deadline'] = 0
                ai_panel['risk_deadline_text'] = f'V pořádku, zbývá {days_until} dní'
        except:
            pass
    
    # Material missing
    for mat in materials:
        stock = mat.get('stock_qty') or 0
        needed = mat.get('qty') or 0
        if stock < needed:
            ai_panel['material_missing'].append({
                'name': mat['name'],
                'needed': needed,
                'available': stock,
                'shortage': needed - stock
            })
    
    if ai_panel['material_missing']:
        ai_panel['recommendations'].append({
            'type': 'material',
            'icon': '📦',
            'text': f'Doobjednat {len(ai_panel["material_missing"])} položek materiálu'
        })
    
    # Team overload
    for member in team:
        hours_week = member.get('hours_week') or 0
        if hours_week > 45:
            ai_panel['team_overload'].append({
                'name': member['name'],
                'hours_week': round(hours_week, 1),
                'over_by': round(hours_week - 40, 1)
            })
    
    if ai_panel['team_overload']:
        ai_panel['recommendations'].append({
            'type': 'team',
            'icon': '👥',
            'text': f'Přerozdělit práci - {len(ai_panel["team_overload"])} lidí přetíženo'
        })
    
    # Budget recommendation
    if finance_summary['spent_pct'] > 80 and completion < 80:
        ai_panel['recommendations'].append({
            'type': 'budget',
            'icon': '💰',
            'text': 'Rozpočet téměř vyčerpán, zkontrolovat další výdaje'
        })
    
    # Positive recommendation if all is well
    if not ai_panel['recommendations']:
        ai_panel['recommendations'].append({
            'type': 'success',
            'icon': '✅',
            'text': 'Zakázka probíhá podle plánu'
        })
    
    return jsonify({
        'ok': True,
        'job': job,
        'materials': materials,
        'team': team,
        'timesheets': timesheets_summary,
        'finance': finance_summary,
        'tasks': tasks_summary,
        'ai_panel': ai_panel
    })

print("✅ Jobs 2.0 Overview API loaded")

@jobs_bp.route("/api/jobs/<int:job_id>/ai-insights")
def api_job_ai_insights(job_id):
    """Get AI insights for job detail - health score, risks, recommendations"""
    u, err = require_role(write=False)
    if err: return err
    
    db = get_db()
    
    # Načti základní data zakázky
    job = db.execute("SELECT * FROM jobs WHERE id=?", (job_id,)).fetchone()
    if not job:
        return jsonify({'ok': False, 'error': 'not_found'}), 404
    
    job = dict(job)
    today = datetime.now().date()
    
    # === Materials ===
    materials = []
    try:
        mat_rows = db.execute("""
            SELECT jm.*, wi.quantity as stock_qty, wi.min_quantity, wi.unit_price
            FROM job_materials jm
            LEFT JOIN warehouse_items wi ON wi.name = jm.name
            WHERE jm.job_id = ?
        """, (job_id,)).fetchall()
        materials = [dict(m) for m in mat_rows]
    except:
        pass
    
    # === Team Assignments ===
    team = []
    try:
        team_rows = db.execute("""
            SELECT e.id, e.name, e.role, e.hourly_rate,
                   (SELECT SUM(hours) FROM timesheets WHERE employee_id = e.id AND date >= date('now', '-7 days')) as hours_week,
                   (SELECT SUM(hours) FROM timesheets WHERE employee_id = e.id AND job_id = ?) as hours_on_job
            FROM job_assignments ja
            JOIN employees e ON e.id = ja.employee_id
            WHERE ja.job_id = ?
        """, (job_id, job_id)).fetchall()
        team = [dict(t) for t in team_rows]
    except:
        pass
    
    # === Timesheets Summary ===
    timesheets_summary = {'total_hours': 0, 'total_cost': 0}
    try:
        ts_result = db.execute("""
            SELECT SUM(t.hours) as total_hours
            FROM timesheets t
            WHERE t.job_id = ?
        """, (job_id,)).fetchone()
        timesheets_summary['total_hours'] = round(ts_result['total_hours'] or 0, 1)
        timesheets_summary['total_cost'] = round((ts_result['total_hours'] or 0) * 200, 0)  # Default rate
    except:
        pass
    
    # === Finance Summary ===
    budget = job.get('budget') or job.get('estimated_value') or 0
    if not budget:
        budget = (job.get('budget_labor') or 0) + (job.get('budget_materials') or 0) + \
                 (job.get('budget_equipment') or 0) + (job.get('budget_other') or 0)
    
    actual_labor = timesheets_summary['total_cost']
    actual_materials = sum((m.get('qty') or 0) * (m.get('unit_price') or 0) for m in materials)
    actual_total = actual_labor + actual_materials
    
    spent_pct = round((actual_total / budget * 100) if budget > 0 else 0, 1)
    margin_pct = round(((budget - actual_total) / budget * 100) if budget > 0 else 0, 1)
    
    # === Tasks Summary ===
    tasks_overdue = 0
    tasks_total = 0
    try:
        task_rows = db.execute("""
            SELECT t.status, t.due_date
            FROM tasks t
            WHERE t.job_id = ?
        """, (job_id,)).fetchall()
        
        for task in task_rows:
            tasks_total += 1
            status = (task['status'] or '').lower()
            if task['due_date'] and status not in ('done', 'completed', 'dokončeno'):
                try:
                    due = datetime.strptime(task['due_date'][:10], '%Y-%m-%d').date()
                    if due < today:
                        tasks_overdue += 1
                except:
                    pass
    except:
        pass
    
    # === Calculate Health Score (0-100) ===
    health_score = 100
    risk_score = 0
    
    # Deadline risk
    deadline = job.get('deadline') or job.get('date')
    completion = job.get('completion_percent') or job.get('progress') or 0
    deadline_risk = 0
    deadline_text = ''
    
    if deadline:
        try:
            deadline_dt = datetime.strptime(deadline[:10], '%Y-%m-%d').date()
            days_until = (deadline_dt - today).days
            
            if days_until < 0:
                deadline_risk = 50
                deadline_text = f'Zakázka je {abs(days_until)} dní po termínu!'
            elif days_until <= 3:
                deadline_risk = 30
                deadline_text = f'Zbývá pouze {days_until} dní'
            elif days_until <= 7 and completion < 80:
                deadline_risk = 20
                deadline_text = f'Zbývá {days_until} dní, dokončeno {completion}%'
            elif days_until <= 14:
                deadline_risk = 10
                deadline_text = f'Zbývá {days_until} dní'
        except:
            pass
    
    risk_score += deadline_risk
    
    # Budget risk
    budget_risk = 0
    if spent_pct > 90:
        budget_risk = 40
    elif spent_pct > 80:
        budget_risk = 20
    elif spent_pct > 70:
        budget_risk = 10
    
    risk_score += budget_risk
    
    # Material risk
    material_risk = 0
    missing_materials = []
    for mat in materials:
        stock = mat.get('stock_qty') or 0
        needed = mat.get('qty') or 0
        if stock < needed:
            missing_materials.append({
                'name': mat['name'],
                'needed': needed,
                'available': stock,
                'shortage': needed - stock
            })
    
    if missing_materials:
        material_risk = min(30, len(missing_materials) * 10)
        risk_score += material_risk
    
    # Capacity risk
    capacity_risk = 0
    overloaded_team = []
    for member in team:
        hours_week = member.get('hours_week') or 0
        if hours_week > 45:
            overloaded_team.append({
                'name': member['name'],
                'hours_week': round(hours_week, 1),
                'over_by': round(hours_week - 40, 1)
            })
    
    if overloaded_team:
        capacity_risk = min(20, len(overloaded_team) * 5)
        risk_score += capacity_risk
    
    # Tasks overdue risk
    if tasks_overdue > 0:
        risk_score += min(20, tasks_overdue * 5)
    
    # Health score = 100 - risk_score (with bonuses)
    health_score = max(0, 100 - risk_score)
    if margin_pct > 30:
        health_score = min(100, health_score + 5)
    if not missing_materials:
        health_score = min(100, health_score + 5)
    if not overloaded_team:
        health_score = min(100, health_score + 5)
    
    # === Build Insights List ===
    insights = []
    
    if deadline_risk > 0:
        insights.append({
            'type': 'deadline',
            'score': deadline_risk,
            'text': deadline_text,
            'priority': 'high' if deadline_risk >= 30 else 'medium'
        })
    
    if budget_risk > 0:
        insights.append({
            'type': 'budget',
            'score': budget_risk,
            'text': f'Rozpočet vyčerpán na {spent_pct}%',
            'priority': 'high' if budget_risk >= 30 else 'medium'
        })
    
    if material_risk > 0:
        insights.append({
            'type': 'material',
            'score': material_risk,
            'text': f'Chybí {len(missing_materials)} materiálů',
            'priority': 'medium',
            'details': missing_materials
        })
    
    if capacity_risk > 0:
        insights.append({
            'type': 'capacity',
            'score': capacity_risk,
            'text': f'{len(overloaded_team)} členů týmu přetíženo',
            'priority': 'medium',
            'details': overloaded_team
        })
    
    if tasks_overdue > 0:
        insights.append({
            'type': 'tasks',
            'score': min(20, tasks_overdue * 5),
            'text': f'{tasks_overdue} úkolů po termínu',
            'priority': 'medium'
        })
    
    # === Build Recommendations ===
    recommendations = []
    
    if deadline_risk >= 30:
        recommendations.append({
            'type': 'urgent',
            'icon': '🚨',
            'title': 'Kritický deadline',
            'text': 'Okamžitě kontaktovat klienta a domluvit nový termín',
            'action': 'contact_client'
        })
    elif deadline_risk >= 20:
        recommendations.append({
            'type': 'warning',
            'icon': '⚠️',
            'title': 'Blížící se deadline',
            'text': 'Zvážit posílení týmu nebo přesčasy',
            'action': 'add_resources'
        })
    
    if material_risk > 0:
        recommendations.append({
            'type': 'material',
            'icon': '📦',
            'title': 'Chybí materiál',
            'text': f'Doobjednat {len(missing_materials)} položek materiálu',
            'action': 'order_materials'
        })
    
    if capacity_risk > 0:
        recommendations.append({
            'type': 'team',
            'icon': '👥',
            'title': 'Přetížení týmu',
            'text': f'Přerozdělit práci - {len(overloaded_team)} lidí přetíženo',
            'action': 'redistribute_work'
        })
    
    if budget_risk >= 20 and completion < 80:
        recommendations.append({
            'type': 'budget',
            'icon': '💰',
            'title': 'Rozpočet téměř vyčerpán',
            'text': 'Zkontrolovat další výdaje a optimalizovat náklady',
            'action': 'review_budget'
        })
    
    # Positive recommendation if all is well
    if not recommendations and health_score >= 80:
        recommendations.append({
            'type': 'success',
            'icon': '✅',
            'title': 'Vše v pořádku',
            'text': 'Zakázka probíhá podle plánu',
            'action': None
        })
    
    return jsonify({
        'ok': True,
        'health_score': round(health_score, 0),
        'risk_score': round(risk_score, 0),
        'insights': insights,
        'recommendations': recommendations
    })

@jobs_bp.route("/api/jobs/<int:job_id>/materials", methods=["POST","DELETE"])
def api_job_materials(job_id):
    u, err = require_role(write=True)
    if err: return err
    db = get_db()
    if request.method == "POST":
        try:
            data = request.get_json(force=True, silent=True) or {}
            name = (data.get("name") or "").strip()
            qty  = float(data.get("qty") or 0)
            unit = (data.get("unit") or "ks").strip()
            if not name: return jsonify({"ok": False, "error":"invalid_input"}), 400
            db.execute("INSERT INTO job_materials(job_id,name,qty,unit) VALUES (?,?,?,?)", (job_id, name, qty, unit))
            db.commit()
            print(f"✓ Material '{name}' added to job {job_id}")
            return jsonify({"ok": True})
        except Exception as e:
            db.rollback()
            print(f"✗ Error adding material: {e}")
            return jsonify({"ok": False, "error": str(e)}), 500
    try:
        mid = request.args.get("id", type=int)
        if not mid: return jsonify({"ok": False, "error":"missing_id"}), 400
        db.execute("DELETE FROM job_materials WHERE id=? AND job_id=?", (mid, job_id))
        db.commit()
        print(f"✓ Material {mid} deleted from job {job_id}")
        return jsonify({"ok": True})
    except Exception as e:
        db.rollback()
        print(f"✗ Error deleting material: {e}")
        return jsonify({"ok": False, "error": str(e)}), 500

@jobs_bp.route("/api/jobs/<int:job_id>/tools", methods=["POST","DELETE"])
def api_job_tools(job_id):
    u, err = require_role(write=True)
    if err: return err
    db = get_db()
    if request.method == "POST":
        try:
            data = request.get_json(force=True, silent=True) or {}
            name = (data.get("name") or "").strip()
            qty  = float(data.get("qty") or 0)
            unit = (data.get("unit") or "ks").strip()
            if not name: return jsonify({"ok": False, "error":"invalid_input"}), 400
            db.execute("INSERT INTO job_tools(job_id,name,qty,unit) VALUES (?,?,?,?)", (job_id, name, qty, unit))
            db.commit()
            print(f"✓ Tool '{name}' added to job {job_id}")
            return jsonify({"ok": True})
        except Exception as e:
            db.rollback()
            print(f"✗ Error adding tool: {e}")
            return jsonify({"ok": False, "error": str(e)}), 500
    try:
        tid = request.args.get("id", type=int)
        if not tid: return jsonify({"ok": False, "error":"missing_id"}), 400
        db.execute("DELETE FROM job_tools WHERE id=? AND job_id=?", (tid, job_id))
        db.commit()
        print(f"✓ Tool {tid} deleted from job {job_id}")
        return jsonify({"ok": True})
    except Exception as e:
        db.rollback()
        print(f"✗ Error deleting tool: {e}")
        return jsonify({"ok": False, "error": str(e)}), 500

@jobs_bp.route("/api/jobs/<int:job_id>/assignments", methods=["POST"])
def api_job_assignments(job_id):
    u, err = require_role(write=True)
    if err: return err
    db = get_db()
    try:
        data = request.get_json(force=True, silent=True) or {}
        ids = data.get("employee_ids") or data.get("assignments") or []
        db.execute("DELETE FROM job_assignments WHERE job_id=?", (job_id,))
        for eid in ids:
            db.execute("INSERT OR IGNORE INTO job_assignments(job_id, employee_id) VALUES (?,?)", (job_id, int(eid)))
        db.commit()
        print(f"✓ Assignments updated for job {job_id}")
        return jsonify({"ok": True})
    except Exception as e:
        db.rollback()
        print(f"✗ Error updating assignments: {e}")
        return jsonify({"ok": False, "error": str(e)}), 500

# ----------------- Tasks CRUD -----------------
@jobs_bp.route("/api/tasks", methods=["GET","POST","PATCH","PUT","DELETE"])
def api_tasks():
    u, err = require_role(write=(request.method!="GET"))
    if err: return err
    db = get_db()

    if request.method == "GET":
        task_id = request.args.get("id", type=int)
        if task_id:
            # Return single task by ID
            row = db.execute("""SELECT t.id, t.job_id, t.employee_id, t.title, t.description, t.status, t.due_date, t.priority,
                                      e.name AS employee_name
                               FROM tasks t
                               LEFT JOIN employees e ON e.id=t.employee_id
                               WHERE t.id=?""", (task_id,)).fetchone()
            if not row:
                return jsonify({"ok": False, "error": "not_found"}), 404
            
            task = {
                "id": row["id"],
                "job_id": row["job_id"],
                "employee_id": row["employee_id"],
                "title": row["title"],
                "description": row["description"],
                "status": row["status"],
                "due_date": row["due_date"],
                "priority": row["priority"] if "priority" in row.keys() else "medium",
                "employee_name": row["employee_name"]
            }
            task["assignees"] = get_task_assignees(db, task_id)
            return jsonify({"ok": True, "task": task})
        
        jid = request.args.get("job_id", type=int)
        employee_id = request.args.get("employee_id", type=int)
        
        q = """SELECT t.id, t.job_id, t.employee_id, t.title, t.description, t.status, t.due_date, t.priority,
                      e.name AS employee_name
               FROM tasks t
               LEFT JOIN employees e ON e.id=t.employee_id"""
        conds=[]; params=[]
        if jid: conds.append("t.job_id=?"); params.append(jid)
        if employee_id:
            # Pokud je zadán employee_id, hledej přes assignments
            q = """SELECT DISTINCT t.id, t.job_id, t.employee_id, t.title, t.description, t.status, t.due_date, t.priority,
                          e.name AS employee_name
                   FROM tasks t
                   LEFT JOIN employees e ON e.id=t.employee_id
                   LEFT JOIN task_assignments ta ON ta.task_id = t.id"""
            conds.append("(t.employee_id=? OR ta.employee_id=?)")
            params.extend([employee_id, employee_id])
        if conds: q += " WHERE " + " AND ".join(conds)
        q += " ORDER BY COALESCE(t.due_date,''), t.id ASC"
        rows = db.execute(q, params).fetchall()
        
        # Vytvoř dictionary pro každý task s explicitním přidáním priority
        tasks = []
        for row in rows:
            task = {
                "id": row["id"],
                "job_id": row["job_id"],
                "employee_id": row["employee_id"],
                "title": row["title"],
                "description": row["description"],
                "status": row["status"],
                "due_date": row["due_date"],
                "priority": row["priority"] if "priority" in row.keys() else "medium",
                "employee_name": row["employee_name"]
            }
            task["assignees"] = get_task_assignees(db, task["id"])
            tasks.append(task)
        
        return jsonify({"ok": True, "tasks": tasks})

    if request.method == "POST":
        try:
            data = request.get_json(force=True, silent=True) or {}
            title = (data.get("title") or "").strip()
            if not title: return jsonify({"ok": False, "error":"invalid_input"}), 400
            
            # Vytvoř úkol
            db.execute("""
                INSERT INTO tasks(job_id, employee_id, title, description, status, due_date, created_by, created_at, updated_at)
                VALUES (?,?,?,?,?,?,?,datetime('now'),datetime('now'))
            """, (
                int(data.get("job_id")) if data.get("job_id") else None,
                int(data.get("employee_id")) if data.get("employee_id") else None,
                title,
                (data.get("description") or "").strip(),
                (data.get("status") or "open"),
                _normalize_date(data.get("due_date")) if data.get("due_date") else None,
                u["id"]
            ))
            db.commit()
            
            # Získej ID nového úkolu
            task_id = db.execute("SELECT last_insert_rowid()").fetchone()[0]
            
            # Přiřaď zaměstnance (pokud jsou zadáni)
            assigned_ids = data.get("assigned_employees", [])
            primary_id = data.get("primary_employee")
            
            if assigned_ids:
                # Expand assignees with one-hop delegates (employee card settings)
                expanded_ids, delegations = _expand_assignees_with_delegate(db, assigned_ids)
                assign_employees_to_task(db, task_id, expanded_ids, primary_id)
                db.commit()

                # Notify assignees
                _notify_assignees(
                    "task",
                    task_id,
                    expanded_ids,
                    title="Nový úkol přiřazen",
                    body=f"Úkol: {title}",
                    actor_user_id=u.get("id"),
                )

                # Notify delegate explicitly (so it's clear it's by delegation)
                for d in delegations:
                    create_notification(
                        employee_id=d.get("to"),
                        kind="delegation",
                        title="Úkol delegován",
                        body=f"Úkol '{title}' byl delegován od zaměstnance ID {d.get('from')}",
                        entity_type="task",
                        entity_id=task_id,
                    )
            
            audit_event(u.get("id"), "create", "task", task_id, after={"title": title, "job_id": data.get("job_id"), "employee_id": data.get("employee_id"), "status": data.get("status"), "due_date": data.get("due_date")})
            print(f"✓ Task '{title}' created successfully (ID: {task_id})")
            return jsonify({"ok": True, "id": task_id})
        except Exception as e:
            db.rollback()
            print(f"✗ Error creating task: {e}")
            return jsonify({"ok": False, "error": str(e)}), 500

    if request.method in ("PATCH", "PUT"):
        try:
            data = request.get_json(force=True, silent=True) or {}
            tid = data.get("id") or request.args.get("id", type=int)
            if not tid: return jsonify({"ok": False, "error":"missing_id"}), 400
            allowed = ["title","description","status","due_date","employee_id","job_id"]
            sets=[]; vals=[]
            for k in allowed:
                if k in data:
                    v = _normalize_date(data[k]) if k=="due_date" else data[k]
                    if k in ("employee_id","job_id") and v is not None:
                        v = int(v)
                    sets.append(f"{k}=?"); vals.append(v)
            if sets:
                vals.append(int(tid))
                db.execute("UPDATE tasks SET " + ", ".join(sets) + " WHERE id=?", vals)
                audit_event(u.get("id"), "update", "task", int(tid), meta={"fields": [s.split("=")[0] for s in sets]})
            
            # Update assignments if provided
            if "assigned_employees" in data:
                # Clear existing assignments
                db.execute("DELETE FROM task_assignments WHERE task_id=?", (tid,))
                
                # Add new assignments
                assigned_ids = data.get("assigned_employees", [])
                primary_id = data.get("primary_employee")
                if assigned_ids:
                    expanded_ids, delegations = _expand_assignees_with_delegate(db, assigned_ids)
                    assign_employees_to_task(db, tid, expanded_ids, primary_id)

                    _notify_assignees(
                        "task",
                        int(tid),
                        expanded_ids,
                        title="Úkol aktualizován",
                        body=f"Úkol byl upraven: {data.get('title') or ''}".strip() or "Úkol byl upraven",
                        actor_user_id=u.get("id"),
                    )
                    for d in delegations:
                        create_notification(
                            employee_id=d.get("to"),
                            kind="delegation",
                            title="Úkol delegován",
                            body=f"Úkol ID {tid} byl delegován od zaměstnance ID {d.get('from')}",
                            entity_type="task",
                            entity_id=int(tid),
                        )
            
            db.commit()
            print(f"✓ Task {tid} updated successfully")
            return jsonify({"ok": True})
        except Exception as e:
            db.rollback()
            print(f"✗ Error updating task: {e}")
            return jsonify({"ok": False, "error": str(e)}), 500

    try:
        tid = request.args.get("id", type=int)
        if not tid: return jsonify({"ok": False, "error":"missing_id"}), 400
        # audit snapshot
        before = db.execute("SELECT id, job_id, employee_id, title, description, status, due_date FROM tasks WHERE id=?", (tid,)).fetchone()
        before = dict(before) if before else None
        db.execute("DELETE FROM tasks WHERE id=?", (tid,))
        db.commit()
        audit_event(u.get("id"), "delete", "task", tid, before=before)
        print(f"✓ Task {tid} deleted successfully")
        return jsonify({"ok": True})
    except Exception as e:
        db.rollback()
        print(f"✗ Error deleting task: {e}")
        return jsonify({"ok": False, "error": str(e)}), 500

# issues CRUD
@jobs_bp.route("/api/issues", methods=["GET","POST","PATCH","DELETE"])
def api_issues():
    u, err = require_role(write=(request.method!="GET"))
    if err: return err
    db = get_db()

    if request.method == "GET":
        issue_id = request.args.get("id", type=int)
        if issue_id:
            # Return single issue by ID
            row = db.execute("""
                SELECT i.*, e.name AS assigned_name, u.name AS creator_name
                FROM issues i
                LEFT JOIN employees e ON e.id = i.assigned_to
                LEFT JOIN users u ON u.id = i.created_by
                WHERE i.id = ?
            """, (issue_id,)).fetchone()
            if not row:
                return jsonify({"ok": False, "error": "not_found"}), 404
            
            issue = dict(row)
            issue["assignees"] = get_issue_assignees(db, issue_id)
            return jsonify({"ok": True, "issue": issue})
        
        # List issues with filters
        jid = request.args.get("job_id", type=int)
        assigned_to = request.args.get("assigned_to", type=int)
        status = request.args.get("status")
        
        if assigned_to:
            # Pokud filtrujeme podle přiřazení, použij JOIN přes assignments
            q = """
                SELECT DISTINCT i.*, e.name AS assigned_name, u.name AS creator_name, j.name AS job_name
                FROM issues i
                LEFT JOIN employees e ON e.id = i.assigned_to
                LEFT JOIN users u ON u.id = i.created_by
                LEFT JOIN jobs j ON j.id = i.job_id
                LEFT JOIN issue_assignments ia ON ia.issue_id = i.id
            """
        else:
            q = """
                SELECT i.*, e.name AS assigned_name, u.name AS creator_name, j.name AS job_name
                FROM issues i
                LEFT JOIN employees e ON e.id = i.assigned_to
                LEFT JOIN users u ON u.id = i.created_by
                LEFT JOIN jobs j ON j.id = i.job_id
            """
        
        conds = []
        params = []
        
        if jid:
            conds.append("i.job_id = ?")
            params.append(jid)
        if assigned_to:
            conds.append("(i.assigned_to = ? OR ia.employee_id = ?)")
            params.extend([assigned_to, assigned_to])
        if status:
            conds.append("i.status = ?")
            params.append(status)
        
        if conds:
            q += " WHERE " + " AND ".join(conds)
        
        q += " ORDER BY CASE i.status WHEN 'open' THEN 0 WHEN 'in_progress' THEN 1 ELSE 2 END, i.created_at DESC"
        
        rows = [dict(r) for r in db.execute(q, params).fetchall()]
        
        # Přidej assignees ke každému issue
        for issue in rows:
            issue["assignees"] = get_issue_assignees(db, issue["id"])
        
        return jsonify({"ok": True, "issues": rows})

    if request.method == "POST":
        try:
            data = request.get_json(force=True, silent=True) or {}
            title = (data.get("title") or "").strip()
            job_id = data.get("job_id")
            
            if not title or not job_id:
                return jsonify({"ok": False, "error": "missing_required_fields"}), 400
            
            db.execute("""
                INSERT INTO issues (job_id, title, description, type, status, severity, assigned_to, created_by)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                int(job_id),
                title,
                (data.get("description") or "").strip(),
                data.get("type") or "blocker",
                data.get("status") or "open",
                data.get("severity"),
                int(data["assigned_to"]) if data.get("assigned_to") else None,
                u["id"]
            ))
            db.commit()
            new_id = db.execute("SELECT last_insert_rowid()").fetchone()[0]
            
            # Přiřaď zaměstnance (pokud jsou zadáni)
            assigned_ids = data.get("assigned_employees", [])
            primary_id = data.get("primary_employee")
            
            if assigned_ids:
                expanded_ids, delegations = _expand_assignees_with_delegate(db, assigned_ids)
                assign_employees_to_issue(db, new_id, expanded_ids, primary_id)
                db.commit()

                _notify_assignees(
                    "issue",
                    new_id,
                    expanded_ids,
                    title="Nový problém přiřazen",
                    body=f"Problém: {title}",
                    actor_user_id=u.get("id"),
                )
                for d in delegations:
                    create_notification(
                        employee_id=d.get("to"),
                        kind="delegation",
                        title="Problém delegován",
                        body=f"Problém '{title}' byl delegován od zaměstnance ID {d.get('from')}",
                        entity_type="issue",
                        entity_id=new_id,
                    )
            
            audit_event(u.get("id"), "create", "issue", new_id, after={"title": title, "job_id": int(job_id), "status": data.get("status") or "open", "type": data.get("type") or "blocker"})
            print(f"✓ Issue '{title}' created (ID: {new_id})")
            return jsonify({"ok": True, "id": new_id})
        except Exception as e:
            db.rollback()
            print(f"✗ Error creating issue: {e}")
            return jsonify({"ok": False, "error": str(e)}), 500

    if request.method == "PATCH":
        try:
            data = request.get_json(force=True, silent=True) or {}
            issue_id = data.get("id") or request.args.get("id", type=int)
            
            if not issue_id:
                return jsonify({"ok": False, "error": "missing_id"}), 400
            
            allowed = ["title", "description", "type", "status", "severity", "assigned_to"]
            sets = []
            vals = []
            
            for k in allowed:
                if k in data:
                    v = data[k]
                    if k == "assigned_to" and v is not None:
                        v = int(v)
                    sets.append(f"{k} = ?")
                    vals.append(v)
            
            # Auto-set resolved_at when status changes to resolved
            if "status" in data and data["status"] == "resolved":
                sets.append("resolved_at = datetime('now')")
            elif "status" in data and data["status"] != "resolved":
                sets.append("resolved_at = NULL")
            
            sets.append("updated_at = datetime('now')")
            
            if sets:
                vals.append(int(issue_id))
                db.execute("UPDATE issues SET " + ", ".join(sets) + " WHERE id = ?", vals)
            
            # Update assignments if provided
            if "assigned_employees" in data:
                # Clear existing assignments
                db.execute("DELETE FROM issue_assignments WHERE issue_id=?", (issue_id,))
                
                # Add new assignments
                assigned_ids = data.get("assigned_employees", [])
                primary_id = data.get("primary_employee")
                if assigned_ids:
                    expanded_ids, delegations = _expand_assignees_with_delegate(db, assigned_ids)
                    assign_employees_to_issue(db, issue_id, expanded_ids, primary_id)

                    _notify_assignees(
                        "issue",
                        int(issue_id),
                        expanded_ids,
                        title="Problém aktualizován",
                        body=f"Problém byl upraven: {data.get('title') or ''}".strip() or "Problém byl upraven",
                        actor_user_id=u.get("id"),
                    )
                    for d in delegations:
                        create_notification(
                            employee_id=d.get("to"),
                            kind="delegation",
                            title="Problém delegován",
                            body=f"Problém ID {issue_id} byl delegován od zaměstnance ID {d.get('from')}",
                            entity_type="issue",
                            entity_id=int(issue_id),
                        )
            
            db.commit()
            print(f"✓ Issue {issue_id} updated")
            return jsonify({"ok": True})
        except Exception as e:
            db.rollback()
            print(f"✗ Error updating issue: {e}")
            return jsonify({"ok": False, "error": str(e)}), 500

    if request.method == "DELETE":
        try:
            issue_id = request.args.get("id", type=int)
            if not issue_id:
                return jsonify({"ok": False, "error": "missing_id"}), 400
            
            # audit snapshot
            before = db.execute("SELECT id, job_id, title, description, type, status, severity, assigned_to FROM issues WHERE id=?", (issue_id,)).fetchone()
            before = dict(before) if before else None
            db.execute("DELETE FROM issues WHERE id = ?", (issue_id,))
            db.commit()
            audit_event(u.get("id"), "delete", "issue", issue_id, before=before)
            print(f"✓ Issue {issue_id} deleted")
            return jsonify({"ok": True})
        except Exception as e:
            db.rollback()
            print(f"✗ Error deleting issue: {e}")
            return jsonify({"ok": False, "error": str(e)}), 500

# job_employees API - přiřazení zaměstnanců k zakázkám
@jobs_bp.route("/api/job_employees", methods=["GET"])
def api_job_employees():
    u, err = require_role(write=False)
    if err: return err
    db = get_db()
    
    job_id = request.args.get("job_id", type=int)
    employee_id = request.args.get("employee_id", type=int)
    
    q = """SELECT je.*, e.name as employee_name, j.client as job_name
           FROM job_employees je
           LEFT JOIN employees e ON e.id = je.employee_id
           LEFT JOIN jobs j ON j.id = je.job_id"""
    conds = []
    params = []
    
    if job_id:
        conds.append("je.job_id = ?")
        params.append(job_id)
    if employee_id:
        conds.append("je.employee_id = ?")
        params.append(employee_id)
    
    if conds:
        q += " WHERE " + " AND ".join(conds)
    
    rows = db.execute(q, params).fetchall()
    return jsonify([dict(r) for r in rows])

# timesheets CRUD + export
@jobs_bp.route("/api/timesheets", methods=["GET","POST","PATCH","DELETE"])
def api_timesheets():
    u, err = require_role(write=(request.method!="GET"))
    if err: return err
    db = get_db()

    if request.method == "GET":
        emp = request.args.get("employee_id", type=int)
        jid = request.args.get("job_id", type=int)
        task_id = request.args.get("task_id", type=int)
        d_from = _normalize_date(request.args.get("from"))
        d_to   = _normalize_date(request.args.get("to"))
        title_col = _job_title_col()
        
        # Zkontroluj existující sloupce
        timesheet_cols = [r[1] for r in db.execute("PRAGMA table_info(timesheets)").fetchall()]
        
        # Sestav SELECT s novými sloupci
        base_cols = "t.id,t.employee_id,t.job_id,t.date,t.hours,t.place,t.activity"
        new_cols = []
        
        if 'duration_minutes' in timesheet_cols:
            new_cols.append("COALESCE(t.duration_minutes, CAST(t.hours * 60 AS INTEGER)) AS duration_minutes")
        if 'labor_cost' in timesheet_cols:
            new_cols.append("COALESCE(t.labor_cost, 0) AS labor_cost")
        if 'work_type' in timesheet_cols:
            new_cols.append("t.work_type")
        if 'start_time' in timesheet_cols:
            new_cols.append("t.start_time")
        if 'end_time' in timesheet_cols:
            new_cols.append("t.end_time")
        if 'location' in timesheet_cols:
            new_cols.append("COALESCE(t.location, t.place) AS location")
        if 'task_id' in timesheet_cols:
            new_cols.append("t.task_id")
        if 'material_used' in timesheet_cols:
            new_cols.append("t.material_used")
        if 'weather_snapshot' in timesheet_cols:
            new_cols.append("t.weather_snapshot")
        if 'performance_signal' in timesheet_cols:
            new_cols.append("t.performance_signal")
        if 'delay_reason' in timesheet_cols:
            new_cols.append("t.delay_reason")
        if 'delay_note' in timesheet_cols:
            new_cols.append("t.delay_note")
        if 'photo_url' in timesheet_cols:
            new_cols.append("t.photo_url")
        if 'note' in timesheet_cols:
            new_cols.append("COALESCE(t.note, t.activity) AS note")
        if 'ai_flags' in timesheet_cols:
            new_cols.append("t.ai_flags")
        if 'created_at' in timesheet_cols:
            new_cols.append("t.created_at")
        
        all_cols = base_cols
        if new_cols:
            all_cols += "," + ",".join(new_cols)
        
        q = f"""SELECT {all_cols},
                      e.name AS employee_name, j.{title_col} AS job_title, j.code AS job_code
               FROM timesheets t
               LEFT JOIN employees e ON e.id=t.employee_id
               LEFT JOIN jobs j ON j.id=t.job_id"""
        conds=[]; params=[]
        if emp: conds.append("t.employee_id=?"); params.append(emp)
        if jid: conds.append("t.job_id=?"); params.append(jid)
        if task_id: conds.append("t.task_id=?"); params.append(task_id)
        if d_from and d_to:
            conds.append("date(t.date) BETWEEN date(?) AND date(?)"); params.extend([d_from, d_to])
        elif d_from:
            conds.append("date(t.date) >= date(?)"); params.append(d_from)
        elif d_to:
            conds.append("date(t.date) <= date(?)"); params.append(d_to)
        if conds: q += " WHERE " + " AND ".join(conds)
        q += " ORDER BY t.date ASC, t.id ASC"
        rows = db.execute(q, params).fetchall()
        
        # Parsuj JSON sloupce
        import json as json_lib
        result_rows = []
        for r in rows:
            row_dict = dict(r)
            # Parsuj JSON sloupce
            for json_col in ['material_used', 'weather_snapshot', 'ai_flags']:
                if json_col in row_dict and row_dict[json_col]:
                    try:
                        row_dict[json_col] = json_lib.loads(row_dict[json_col])
                    except:
                        row_dict[json_col] = None
            result_rows.append(row_dict)
        
        return jsonify({"ok": True, "rows": result_rows})

    if request.method == "POST":
        try:
            import json as json_lib
            data = request.get_json(force=True, silent=True) or {}
            emp = data.get("employee_id")
            job = data.get("job_id")  # Může být None nebo 0
            dt = data.get("date")
            hours = data.get("hours")
            duration_minutes = data.get("duration_minutes")
            
            # Validace povinných polí
            if not emp or not dt:
                return jsonify({"ok": False, "error": "missing_required_fields"}), 400
            
            # job_id může být None/0 pro výkazy bez zakázky
            if job is None:
                job = 0
            
            # Vypočti duration_minutes z hours pokud není zadáno
            if duration_minutes is None:
                if hours is not None:
                    duration_minutes = int(float(hours) * 60)
                else:
                    duration_minutes = 480  # default 8h
            
            # Vypočti hours z duration_minutes pokud není zadáno
            if hours is None:
                hours = duration_minutes / 60.0
            
            # Stará pole (zpětná kompatibilita)
            place = data.get("place") or data.get("location") or ""
            activity = data.get("activity") or data.get("note") or ""
            
            # Nová pole
            user_id = data.get("user_id")
            work_type = data.get("work_type") or "manual"
            start_time = data.get("start_time")
            end_time = data.get("end_time")
            location = data.get("location") or place
            task_id = data.get("task_id")
            material_used = json_lib.dumps(data.get("material_used")) if data.get("material_used") else None
            weather_snapshot = json_lib.dumps(data.get("weather_snapshot")) if data.get("weather_snapshot") else None
            performance_signal = data.get("performance_signal") or "normal"
            delay_reason = data.get("delay_reason")
            delay_note = data.get("delay_note")
            photo_url = data.get("photo_url")
            note = data.get("note") or activity
            
            # Vypočti labor_cost
            labor_cost = calculate_labor_cost(int(emp), int(job) if job else None, duration_minutes, db)
            
            # Detekuj anomálie
            ai_flags_data = detect_anomalies({
                'duration_minutes': duration_minutes,
                'performance_signal': performance_signal,
                'delay_reason': delay_reason
            }, db)
            ai_flags = json_lib.dumps(ai_flags_data)
            
            # Vložení do DB
            cols = ["employee_id", "job_id", "date", "hours", "duration_minutes", "place", "activity"]
            vals = [int(emp), int(job), _normalize_date(dt), float(hours), duration_minutes, place, activity]
            
            # Přidej nová pole pokud existují sloupce
            timesheet_cols = [r[1] for r in db.execute("PRAGMA table_info(timesheets)").fetchall()]
            
            if 'user_id' in timesheet_cols:
                cols.append("user_id"); vals.append(int(user_id) if user_id else None)
            if 'work_type' in timesheet_cols:
                cols.append("work_type"); vals.append(work_type)
            if 'start_time' in timesheet_cols:
                cols.append("start_time"); vals.append(start_time)
            if 'end_time' in timesheet_cols:
                cols.append("end_time"); vals.append(end_time)
            if 'location' in timesheet_cols:
                cols.append("location"); vals.append(location)
            if 'task_id' in timesheet_cols:
                cols.append("task_id"); vals.append(int(task_id) if task_id else None)
            if 'material_used' in timesheet_cols:
                cols.append("material_used"); vals.append(material_used)
            if 'weather_snapshot' in timesheet_cols:
                cols.append("weather_snapshot"); vals.append(weather_snapshot)
            if 'performance_signal' in timesheet_cols:
                cols.append("performance_signal"); vals.append(performance_signal)
            if 'delay_reason' in timesheet_cols:
                cols.append("delay_reason"); vals.append(delay_reason)
            if 'delay_note' in timesheet_cols:
                cols.append("delay_note"); vals.append(delay_note)
            if 'photo_url' in timesheet_cols:
                cols.append("photo_url"); vals.append(photo_url)
            if 'note' in timesheet_cols:
                cols.append("note"); vals.append(note)
            if 'ai_flags' in timesheet_cols:
                cols.append("ai_flags"); vals.append(ai_flags)
            if 'labor_cost' in timesheet_cols:
                cols.append("labor_cost"); vals.append(labor_cost)
            
            placeholders = ",".join("?" * len(vals))
            db.execute(f"INSERT INTO timesheets({','.join(cols)}) VALUES ({placeholders})", vals)
            db.commit()
            
            # Získat ID nového výkazu
            new_id = db.execute("SELECT last_insert_rowid()").fetchone()[0]
            
            # Zpracuj materiál
            if material_used:
                process_material_usage(new_id, data.get("material_used"), None, db)
            
            # Přepočti statistiky zakázky
            if job:
                recalculate_job_stats(int(job), db)
            
            print(f"✓ Timesheet {new_id} created successfully (emp:{emp}, job:{job}, date:{dt})")
            return jsonify({"ok": True, "id": new_id})
        except Exception as e:
            db.rollback()
            print(f"✗ Error creating timesheet: {e}")
            import traceback
            traceback.print_exc()
            return jsonify({"ok": False, "error": str(e)}), 500

    if request.method == "PATCH":
        try:
            import json as json_lib
            data = request.get_json(force=True, silent=True) or {}
            tid = data.get("id")
            if not tid:
                return jsonify({"ok": False, "error": "missing_id"}), 400
            
            # Získej starý výkaz pro delta materiálu
            old_row = db.execute("SELECT job_id, material_used FROM timesheets WHERE id=?", (tid,)).fetchone()
            old_job_id = old_row[0] if old_row else None
            old_material = old_row[1] if old_row and old_row[1] else None
            
            # Získej existující sloupce
            timesheet_cols = [r[1] for r in db.execute("PRAGMA table_info(timesheets)").fetchall()]
            
            # Povolená pole (stará + nová)
            allowed = ["employee_id", "job_id", "date", "hours", "duration_minutes", "place", "activity",
                      "location", "note", "work_type", "start_time", "end_time", "task_id",
                      "material_used", "weather_snapshot", "performance_signal", "delay_reason",
                      "delay_note", "photo_url"]
            
            sets, vals = [], []
            
            # Zpracuj každé pole
            for k in allowed:
                if k not in data:
                    continue
                
                # Zkontroluj existenci sloupce
                if k not in timesheet_cols and k not in ["hours", "place", "activity"]:
                    continue
                
                v = data[k]
                
                # Speciální zpracování podle typu
                if k == "date":
                    v = _normalize_date(v)
                elif k in ("employee_id", "job_id", "task_id"):
                    v = int(v) if v else None
                elif k == "hours":
                    v = float(v) if v is not None else None
                elif k == "duration_minutes":
                    v = int(v) if v is not None else None
                elif k in ("material_used", "weather_snapshot", "ai_flags"):
                    v = json_lib.dumps(v) if v else None
                
                sets.append(f"{k}=?"); vals.append(v)
            
            # Přepočti duration_minutes z hours nebo naopak
            if "hours" in data and "duration_minutes" not in data:
                hours_val = float(data["hours"]) if data["hours"] is not None else None
                if hours_val is not None and "duration_minutes" in timesheet_cols:
                    sets.append("duration_minutes=?"); vals.append(int(hours_val * 60))
            elif "duration_minutes" in data and "hours" not in data:
                mins_val = int(data["duration_minutes"]) if data["duration_minutes"] is not None else None
                if mins_val is not None:
                    sets.append("hours=?"); vals.append(mins_val / 60.0)
            
            # Přepočti labor_cost pokud se změnily relevantní hodnoty
            if any(k in data for k in ["employee_id", "job_id", "duration_minutes", "hours"]):
                emp = data.get("employee_id")
                job = data.get("job_id")
                duration = data.get("duration_minutes")
                
                if not emp:
                    old_emp = db.execute("SELECT employee_id FROM timesheets WHERE id=?", (tid,)).fetchone()
                    emp = old_emp[0] if old_emp else None
                
                if not job and old_job_id:
                    job = old_job_id
                
                if not duration:
                    old_dur = db.execute("SELECT duration_minutes, hours FROM timesheets WHERE id=?", (tid,)).fetchone()
                    if old_dur:
                        duration = old_dur[0] if old_dur[0] else int(old_dur[1] * 60) if old_dur[1] else 480
                
                if emp and duration and "labor_cost" in timesheet_cols:
                    labor_cost = calculate_labor_cost(int(emp), int(job) if job else None, duration, db)
                    sets.append("labor_cost=?"); vals.append(labor_cost)
            
            # Aktualizuj AI flags
            if any(k in data for k in ["duration_minutes", "hours", "performance_signal", "delay_reason"]):
                old_row = db.execute(
                    "SELECT duration_minutes, hours, performance_signal, delay_reason FROM timesheets WHERE id=?",
                    (tid,)
                ).fetchone()
                
                duration_for_flags = data.get("duration_minutes") or (old_row[0] if old_row else None) or (int((data.get("hours") or (old_row[1] if old_row else 0)) * 60))
                perf_signal = data.get("performance_signal") or (old_row[2] if old_row else "normal")
                delay_reason = data.get("delay_reason") or (old_row[3] if old_row else None)
                
                if "ai_flags" in timesheet_cols:
                    ai_flags_data = detect_anomalies({
                        'duration_minutes': duration_for_flags,
                        'performance_signal': perf_signal,
                        'delay_reason': delay_reason
                    }, db)
                    sets.append("ai_flags=?"); vals.append(json_lib.dumps(ai_flags_data))
            
            if not sets:
                return jsonify({"ok": False, "error": "no_fields"}), 400
            
            vals.append(int(tid))
            db.execute("UPDATE timesheets SET " + ",".join(sets) + " WHERE id=?", vals)
            db.commit()
            
            # Zpracuj změny materiálu
            if "material_used" in data:
                new_material = data.get("material_used")
                process_material_usage(tid, new_material, old_material, db)
            
            # Přepočti statistiky zakázky (stará i nová)
            new_job_id = data.get("job_id", old_job_id)
            if new_job_id:
                recalculate_job_stats(int(new_job_id), db)
            if old_job_id and old_job_id != new_job_id:
                recalculate_job_stats(int(old_job_id), db)
            
            print(f"✓ Timesheet {tid} updated successfully")
            return jsonify({"ok": True})
        except Exception as e:
            db.rollback()
            print(f"✗ Error updating timesheet: {e}")
            import traceback
            traceback.print_exc()
            return jsonify({"ok": False, "error": str(e)}), 500

    # DELETE
    try:
        tid = request.args.get("id", type=int)
        if not tid:
            return jsonify({"ok": False, "error": "missing_id"}), 400
        
        # Získej data před smazáním pro reverz materiálu
        old_row = db.execute(
            "SELECT job_id, material_used FROM timesheets WHERE id=?",
            (tid,)
        ).fetchone()
        
        old_job_id = old_row[0] if old_row else None
        old_material = old_row[1] if old_row else None
        
        # Vrať materiál do skladu
        if old_material:
            try:
                import json as json_lib
                material_list = json_lib.loads(old_material) if isinstance(old_material, str) else old_material
                if material_list:
                    process_material_usage(tid, [], material_list, db)  # Reverz: odečti zápornou deltu
            except Exception as e:
                print(f"Warning: Could not reverse material usage: {e}")
        
        # Smaž výkaz
        db.execute("DELETE FROM timesheets WHERE id=?", (tid,))
        db.commit()
        
        # Přepočti statistiky zakázky
        if old_job_id:
            recalculate_job_stats(int(old_job_id), db)
        
        print(f"✓ Timesheet {tid} deleted successfully")
        return jsonify({"ok": True})
    except Exception as e:
        db.rollback()
        print(f"✗ Error deleting timesheet: {e}")
        return jsonify({"ok": False, "error": str(e)}), 500

# ----------------- Worklog Service Layer -----------------
def page_jobs():
    return send_from_directory(".", "jobs.html")

@jobs_bp.route("/tasks.html")
def page_tasks():
    return send_from_directory(".", "tasks.html")

@jobs_bp.route("/issues")
@jobs_bp.route("/api/admin/download-db", methods=["GET"])
@requires_role('owner', 'admin')
def api_admin_download_db():
    """Stáhne aktuální SQLite databázi jako soubor (pouze owner/admin)."""
    db_path = os.environ.get("DB_PATH") or "/var/data/app.db"
    if not os.path.exists(db_path):
        return jsonify({"ok": False, "error": "db_not_found", "path": db_path}), 404
    return send_file(db_path, as_attachment=True, download_name="app.db")

@jobs_bp.route("/api/admin/export-all", methods=["GET"])
@requires_role('owner', 'admin')
def api_job_material_delete(job_id, material_id):
    """Smazání materiálu ze zakázky (automaticky uvolní rezervaci ze skladu)"""
    u, err = require_auth()
    if err: return err
    if u["role"] not in WRITE_ROLES:
        return jsonify({"error": "Forbidden"}), 403
    
    try:
        db = get_db()
        
        # Načti materiál (pro kontrolu)
        material = db.execute("""
            SELECT warehouse_item_id, reserved_qty, status 
            FROM job_materials 
            WHERE id = ? AND job_id = ?
        """, (material_id, job_id)).fetchone()
        
        if not material:
            return jsonify({"error": "Material not found"}), 404
        
        # Smaž materiál (trigger automaticky upraví reserved_qty ve warehouse_items)
        db.execute("""
            DELETE FROM job_materials 
            WHERE id = ? AND job_id = ?
        """, (material_id, job_id))
        
        db.commit()
        
        message = "Material deleted"
        if material["warehouse_item_id"]:
            message += " and reservation released"
        
        return jsonify({"ok": True, "message": message})
    except Exception as e:
        db.rollback()
        print(f"[ERROR] delete_material: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

@jobs_bp.route("/api/jobs/<int:job_id>/materials/<int:material_id>/release", methods=["POST"])
def api_job_release_material(job_id, material_id):
    """Uvolnění materiálu z zakázky zpět do skladu"""
    u, err = require_auth()
    if err: return err
    if u["role"] not in WRITE_ROLES:
        return jsonify({"error": "Forbidden"}), 403
    
    try:
        db = get_db()
        
        # Načti materiál
        material = db.execute("""
            SELECT warehouse_item_id, reserved_qty 
            FROM job_materials 
            WHERE id = ? AND job_id = ?
        """, (material_id, job_id)).fetchone()
        
        if not material:
            return jsonify({"error": "Material not found"}), 404
        
        # Pokud je propojený se skladem, uvolni rezervaci
        if material["warehouse_item_id"]:
            db.execute("""
                UPDATE warehouse_items 
                SET reserved_qty = reserved_qty - ?,
                    updated_at = datetime('now')
                WHERE id = ?
            """, (material["reserved_qty"] or 0, material["warehouse_item_id"]))
        
        # Smaž z job_materials
        db.execute("DELETE FROM job_materials WHERE id = ? AND job_id = ?", (material_id, job_id))
        
        db.commit()
        return jsonify({"ok": True, "message": "Material released successfully"})
    except Exception as e:
        db.rollback()
        print(f"[ERROR] release_material: {e}")
        return jsonify({"error": str(e)}), 500

@jobs_bp.route("/api/warehouse/items/<int:item_id>/reservations", methods=["GET"])
def api_warehouse_item_reservations(item_id):
    """Zobrazení všech rezervací pro položku skladu"""
    u, err = require_auth()
    if err: return err
    
    try:
        db = get_db()
        
        reservations = db.execute("""
            SELECT 
                jm.id, jm.job_id, jm.qty, jm.reserved_qty,
                j.title as job_title, j.code as job_code, j.status as job_status
            FROM job_materials jm
            JOIN jobs j ON jm.job_id = j.id
            WHERE jm.warehouse_item_id = ?
            ORDER BY j.date DESC
        """, (item_id,)).fetchall()
        
        result = []
        for r in reservations:
            result.append({
                "id": r["id"],
                "job_id": r["job_id"],
                "job_title": r["job_title"],
                "job_code": r["job_code"],
                "job_status": r["job_status"],
                "qty": r["qty"],
                "reserved_qty": r["reserved_qty"]
            })
        
        return jsonify({"reservations": result})
    except Exception as e:
        print(f"[ERROR] get_reservations: {e}")
        return jsonify({"error": str(e)}), 500



# ========== PLANT CATALOG API ==========

@jobs_bp.route('/api/plant-catalog/search', methods=['GET'])
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


@jobs_bp.route('/api/plant-catalog/<int:plant_id>', methods=['GET'])
def api_plant_catalog_detail(plant_id):
    """Detail rostliny z katalogu"""
    u, err = require_auth()
    if err: return err
    
    try:
        db = get_db()
        plant = db.execute('''
            SELECT * FROM plant_catalog WHERE id = ?
        ''', (plant_id,)).fetchone()
        
        if not plant:
            return jsonify({
                'success': False,
                'message': 'Rostlina nenalezena'
            }), 404
        
        return jsonify({
            'success': True,
            'plant': dict(plant)
        })
        
    except Exception as e:
        print(f"[ERROR] plant_catalog_detail: {e}")
        return jsonify({
            'success': False,
            'message': f'Chyba při načítání: {str(e)}'
        }), 500


@jobs_bp.route('/api/plant-catalog/stats', methods=['GET'])
def api_plant_catalog_stats():
    """Statistiky katalogu"""
    u, err = require_auth()
    if err: return err
    
    try:
        db = get_db()
        
        stats = db.execute('''
            SELECT 
                COUNT(*) as total_plants,
                COUNT(DISTINCT latin_name) as species_count,
                COUNT(DISTINCT CASE WHEN variety IS NOT NULL THEN latin_name END) as varieties_count
            FROM plant_catalog
        ''').fetchone()
        
        return jsonify({
            'success': True,
            'stats': dict(stats)
        })
        
    except Exception as e:
        print(f"[ERROR] plant_catalog_stats: {e}")
        return jsonify({
            'success': False,
            'message': f'Chyba: {str(e)}'
        }), 500


@jobs_bp.route('/api/plant-catalog/by-name', methods=['GET'])
def api_plant_catalog_by_name():
    """Najdi rostlinu přesně podle názvu a odrůdy"""
    u, err = require_auth()
    if err: return err
    
    latin = request.args.get('latin', '').strip()
    variety = request.args.get('variety', '').strip() or None
    
    if not latin:
        return jsonify({
            'success': False,
            'message': 'Chybí latinský název'
        }), 400
    
    try:
        db = get_db()
        
        if variety:
            plant = db.execute('''
                SELECT * FROM plant_catalog 
                WHERE latin_name = ? AND variety = ?
                LIMIT 1
            ''', (latin, variety)).fetchone()
        else:
            plant = db.execute('''
                SELECT * FROM plant_catalog 
                WHERE latin_name = ? AND variety IS NULL
                LIMIT 1
            ''', (latin,)).fetchone()
        
        if plant:
            return jsonify({
                'success': True,
                'plant': dict(plant)
            })
        else:
            return jsonify({
                'success': False,
                'message': 'Rostlina v katalogu nenalezena'
            }), 404
            
    except Exception as e:
        print(f"[ERROR] plant_catalog_by_name: {e}")
        return jsonify({
            'success': False,
            'message': f'Chyba: {str(e)}'
        }), 500


@jobs_bp.route('/api/weather', methods=['GET'])
def api_weather():
    """Získá aktuální počasí pro zadané město (default: Příbram)"""
    u, err = require_auth()
    if err: return err
    
    city = request.args.get('city', 'Příbram')
    
    # Open-Meteo API - free, no API key required
    # Koordináty pro Příbram, CZ
    locations = {
        'Příbram': {'lat': 49.6897, 'lon': 14.0101},
        'Praha': {'lat': 50.0755, 'lon': 14.4378},
        'Brno': {'lat': 49.1951, 'lon': 16.6068},
        'Ostrava': {'lat': 49.8209, 'lon': 18.2625},
        'Plzeň': {'lat': 49.7384, 'lon': 13.3736},
    }
    
    coords = locations.get(city, locations['Příbram'])
    
    try:
        import urllib.request
        import urllib.error
        
        url = f"https://api.open-meteo.com/v1/forecast?latitude={coords['lat']}&longitude={coords['lon']}&current=temperature_2m,relative_humidity_2m,weather_code,wind_speed_10m&daily=weather_code,temperature_2m_max,temperature_2m_min,precipitation_probability_max&timezone=Europe%2FPrague&forecast_days=5"
        
        req = urllib.request.Request(url, headers={'User-Agent': 'GreenDavidApp/1.0'})
        with urllib.request.urlopen(req, timeout=5) as response:
            data = json.loads(response.read().decode('utf-8'))
        
        # Weather code to description and icon
        weather_codes = {
            0: {'desc': 'Jasno', 'icon': '☀️'},
            1: {'desc': 'Převážně jasno', 'icon': '🌤️'},
            2: {'desc': 'Polojasno', 'icon': '⛅'},
            3: {'desc': 'Zataženo', 'icon': '☁️'},
            45: {'desc': 'Mlha', 'icon': '🌫️'},
            48: {'desc': 'Mrznoucí mlha', 'icon': '🌫️'},
            51: {'desc': 'Mrholení', 'icon': '🌧️'},
            53: {'desc': 'Mrholení', 'icon': '🌧️'},
            55: {'desc': 'Mrholení', 'icon': '🌧️'},
            61: {'desc': 'Déšť', 'icon': '🌧️'},
            63: {'desc': 'Déšť', 'icon': '🌧️'},
            65: {'desc': 'Silný déšť', 'icon': '🌧️'},
            71: {'desc': 'Sněžení', 'icon': '🌨️'},
            73: {'desc': 'Sněžení', 'icon': '🌨️'},
            75: {'desc': 'Husté sněžení', 'icon': '🌨️'},
            80: {'desc': 'Přeháňky', 'icon': '🌦️'},
            81: {'desc': 'Přeháňky', 'icon': '🌦️'},
            82: {'desc': 'Silné přeháňky', 'icon': '🌦️'},
            95: {'desc': 'Bouřka', 'icon': '⛈️'},
            96: {'desc': 'Bouřka s krupobitím', 'icon': '⛈️'},
            99: {'desc': 'Bouřka s krupobitím', 'icon': '⛈️'},
        }
        
        current = data.get('current', {})
        daily = data.get('daily', {})
        
        weather_code = current.get('weather_code', 0)
        weather_info = weather_codes.get(weather_code, {'desc': 'Neznámo', 'icon': '❓'})
        
        # Forecast for next days
        forecast = []
        if daily:
            for i in range(min(5, len(daily.get('time', [])))):
                day_code = daily['weather_code'][i] if i < len(daily.get('weather_code', [])) else 0
                day_info = weather_codes.get(day_code, {'desc': 'Neznámo', 'icon': '❓'})
                forecast.append({
                    'date': daily['time'][i],
                    'temp_max': daily['temperature_2m_max'][i] if i < len(daily.get('temperature_2m_max', [])) else None,
                    'temp_min': daily['temperature_2m_min'][i] if i < len(daily.get('temperature_2m_min', [])) else None,
                    'precipitation_prob': daily['precipitation_probability_max'][i] if i < len(daily.get('precipitation_probability_max', [])) else 0,
                    'description': day_info['desc'],
                    'icon': day_info['icon']
                })
        
        # Gardening advice based on weather
        advice = []
        temp = current.get('temperature_2m', 15)
        humidity = current.get('relative_humidity_2m', 50)
        wind = current.get('wind_speed_10m', 0)
        
        if weather_code in [61, 63, 65, 80, 81, 82]:
            advice.append("🌧️ Dnes prší - ideální den pro práci ve skleníku")
        elif weather_code in [71, 73, 75]:
            advice.append("🌨️ Sněží - pozor na mráz, zkontrolujte ochranu rostlin")
        elif weather_code in [0, 1] and temp > 20:
            advice.append("☀️ Horký den - nezapomeňte zavlažovat")
        
        if temp < 5:
            advice.append("🥶 Nízká teplota - pozor na mráz citlivých rostlin")
        elif temp > 30:
            advice.append("🌡️ Tropické teploty - ranní nebo večerní práce doporučena")
        
        if wind > 30:
            advice.append("💨 Silný vítr - odložte postřiky a mulčování")
        
        if humidity > 80 and temp > 15:
            advice.append("💧 Vysoká vlhkost - sledujte plísňové choroby")
        
        return jsonify({
            'success': True,
            'city': city,
            'current': {
                'temperature': current.get('temperature_2m'),
                'humidity': current.get('relative_humidity_2m'),
                'wind_speed': current.get('wind_speed_10m'),
                'weather_code': weather_code,
                'description': weather_info['desc'],
                'icon': weather_info['icon']
            },
            'forecast': forecast,
            'advice': advice
        })
        
    except urllib.error.URLError as e:
        print(f"[WARNING] Weather API network error: {e}")
        return jsonify({
            'success': False,
            'message': 'Nelze načíst počasí - zkontrolujte připojení',
            'offline': True
        }), 503
    except Exception as e:
        print(f"[ERROR] api_weather: {e}")
        return jsonify({
            'success': False,
            'message': f'Chyba při načítání počasí: {str(e)}'
        }), 500


# ==================== DASHBOARD STATS API ====================
@jobs_bp.route('/api/dashboard/stats', methods=['GET'])
def api_dashboard_stats():
    """Rychlé statistiky pro dashboard"""
    u, err = require_auth()
    if err: return err
    
    try:
        db = get_db()
        today = date.today().isoformat()
        week_start = (date.today() - timedelta(days=date.today().weekday())).isoformat()
        
        # Active jobs
        active_jobs = db.execute(
            "SELECT COUNT(*) as cnt FROM jobs WHERE status IN ('Plán', 'Probíhá')"
        ).fetchone()['cnt']
        
        # Pending tasks
        pending_tasks = db.execute(
            "SELECT COUNT(*) as cnt FROM tasks WHERE status IN ('open', 'in-progress')"
        ).fetchone()['cnt']
        
        # Urgent tasks (due today)
        urgent_tasks = db.execute(
            "SELECT COUNT(*) as cnt FROM tasks WHERE due_date = ? AND status != 'completed'",
            (today,)
        ).fetchone()['cnt']
        
        # Hours this week
        hours_week = db.execute(
            "SELECT COALESCE(SUM(hours), 0) as total FROM timesheets WHERE date >= ?",
            (week_start,)
        ).fetchone()['total']
        
        # Employees count
        emp_count = db.execute("SELECT COUNT(*) as cnt FROM employees").fetchone()['cnt']
        
        # Low stock items
        low_stock = db.execute(
            "SELECT COUNT(*) as cnt FROM warehouse_items WHERE quantity <= min_quantity AND min_quantity > 0"
        ).fetchone()['cnt']
        
        return jsonify({
            'success': True,
            'stats': {
                'active_jobs': active_jobs,
                'pending_tasks': pending_tasks,
                'urgent_tasks': urgent_tasks,
                'hours_week': round(hours_week, 1),
                'employee_count': emp_count,
                'low_stock_items': low_stock
            }
        })
        
    except Exception as e:
        print(f"[ERROR] api_dashboard_stats: {e}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500


# ==================== DEADLINE CHECK & NOTIFICATIONS ====================
@jobs_bp.route('/api/check-deadlines', methods=['POST'])
def api_check_deadlines():
    """Check for upcoming deadlines and create notifications.
    Can be called periodically (e.g., once per day via cron or manual trigger).
    """
    u, err = require_auth()
    if err: return err
    
    # Only admin/owner can trigger this
    if normalize_role(u.get("role")) not in ("owner", "admin"):
        return jsonify({"ok": False, "error": "forbidden"}), 403
    
    try:
        db = get_db()
        today = date.today()
        tomorrow = today + timedelta(days=1)
        
        notifications_created = 0
        
        # Tasks due today
        tasks_today = db.execute("""
            SELECT t.id, t.title, t.employee_id, ta.employee_id as assigned_emp
            FROM tasks t
            LEFT JOIN task_assignees ta ON t.id = ta.task_id
            WHERE t.due_date = ? AND t.status != 'completed'
        """, (today.isoformat(),)).fetchall()
        
        for task in tasks_today:
            emp_id = task['assigned_emp'] or task['employee_id']
            if emp_id:
                create_notification(
                    employee_id=emp_id,
                    kind="deadline",
                    title="⏰ Deadline dnes!",
                    body=f"Úkol '{task['title']}' má deadline dnes",
                    entity_type="task",
                    entity_id=task['id']
                )
                notifications_created += 1
        
        # Tasks due tomorrow
        tasks_tomorrow = db.execute("""
            SELECT t.id, t.title, t.employee_id, ta.employee_id as assigned_emp
            FROM tasks t
            LEFT JOIN task_assignees ta ON t.id = ta.task_id
            WHERE t.due_date = ? AND t.status != 'completed'
        """, (tomorrow.isoformat(),)).fetchall()
        
        for task in tasks_tomorrow:
            emp_id = task['assigned_emp'] or task['employee_id']
            if emp_id:
                create_notification(
                    employee_id=emp_id,
                    kind="deadline",
                    title="📅 Deadline zítra",
                    body=f"Úkol '{task['title']}' má deadline zítra",
                    entity_type="task",
                    entity_id=task['id']
                )
                notifications_created += 1
        
        # Jobs ending soon (within 3 days)
        soon = today + timedelta(days=3)
        jobs_soon = db.execute("""
            SELECT id, title, date FROM jobs
            WHERE date BETWEEN ? AND ? AND status != 'Dokončeno'
        """, (today.isoformat(), soon.isoformat())).fetchall()
        
        # Notify all admins about jobs ending soon
        admins = db.execute("SELECT id FROM users WHERE role IN ('owner', 'admin')").fetchall()
        for job in jobs_soon:
            for admin in admins:
                create_notification(
                    user_id=admin['id'],
                    kind="job",
                    title="🏗️ Zakázka končí brzy",
                    body=f"Zakázka '{job['title']}' má termín {job['date']}",
                    entity_type="job",
                    entity_id=job['id']
                )
                notifications_created += 1
        
        # Low stock alerts
        low_stock = db.execute("""
            SELECT id, name, quantity, min_quantity FROM warehouse_items
            WHERE quantity <= min_quantity AND min_quantity > 0
        """).fetchall()
        
        for item in low_stock:
            for admin in admins:
                create_notification(
                    user_id=admin['id'],
                    kind="stock",
                    title="📦 Nízký stav skladu",
                    body=f"'{item['name']}' - zbývá {item['quantity']} ks (min: {item['min_quantity']})",
                    entity_type="warehouse",
                    entity_id=item['id']
                )
                notifications_created += 1
        
        return jsonify({
            'ok': True,
            'notifications_created': notifications_created
        })
        
    except Exception as e:
        print(f"[ERROR] api_check_deadlines: {e}")
        return jsonify({
            'ok': False,
            'error': str(e)
        }), 500


# ==================== QUICK ACTIONS API ====================
@jobs_bp.route('/api/quick-add', methods=['POST'])
def api_quick_add():
    """Rychlé přidání položky (task, note, timesheet) z dashboardu"""
    u, err = require_auth()
    if err: return err
    
    try:
        data = request.get_json(force=True, silent=True) or {}
        item_type = data.get('type', 'task')
        
        db = get_db()
        
        if item_type == 'task':
            title = (data.get('title') or '').strip()
            if not title:
                return jsonify({'ok': False, 'error': 'Zadejte název úkolu'}), 400
            
            db.execute("""
                INSERT INTO tasks(title, status, created_by, created_at, updated_at)
                VALUES (?, 'open', ?, datetime('now'), datetime('now'))
            """, (title, u['id']))
            db.commit()
            task_id = db.execute("SELECT last_insert_rowid()").fetchone()[0]
            
            return jsonify({'ok': True, 'id': task_id, 'type': 'task'})
        
        elif item_type == 'timesheet':
            hours = data.get('hours')
            job_id = data.get('job_id')
            
            if not hours:
                return jsonify({'ok': False, 'error': 'Zadejte počet hodin'}), 400
            
            # Get employee_id for current user
            emp = db.execute("SELECT id FROM employees WHERE user_id = ?", (u['id'],)).fetchone()
            emp_id = emp['id'] if emp else None
            
            db.execute("""
                INSERT INTO timesheets(employee_id, job_id, date, hours, note, created_by)
                VALUES (?, ?, date('now'), ?, ?, ?)
            """, (emp_id, job_id, float(hours), data.get('note', ''), u['id']))
            db.commit()
            
            return jsonify({'ok': True, 'type': 'timesheet'})
        
        return jsonify({'ok': False, 'error': 'Neznámý typ'}), 400
        
    except Exception as e:
        print(f"[ERROR] api_quick_add: {e}")
        return jsonify({'ok': False, 'error': str(e)}), 500


# ============================================================
# GPS CHECK-IN/OUT API
# ============================================================

@jobs_bp.route('/api/gps/checkin', methods=['POST'])
def api_gps_checkin():
    """Record GPS check-in to a job."""
    user, err = require_auth()
    if err:
        return err
    
    try:
        data = request.get_json() or {}
        job_id = data.get('job_id')
        check_in_time = data.get('check_in_time')
        lat = data.get('lat')
        lng = data.get('lng')
        
        if not job_id:
            return jsonify({'ok': False, 'error': 'job_id required'}), 400
        
        db = get_db()
        
        # Create gps_logs table if not exists
        db.execute('''CREATE TABLE IF NOT EXISTS gps_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            job_id INTEGER,
            check_in_time TEXT,
            check_out_time TEXT,
            check_in_lat REAL,
            check_in_lng REAL,
            check_out_lat REAL,
            check_out_lng REAL,
            hours_worked REAL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )''')
        
        db.execute('''
            INSERT INTO gps_logs (user_id, job_id, check_in_time, check_in_lat, check_in_lng)
            VALUES (?, ?, ?, ?, ?)
        ''', [session.get('user_id'), job_id, check_in_time, lat, lng])
        db.commit()
        
        return jsonify({'ok': True, 'message': 'Check-in recorded'})
    except Exception as e:
        print(f"[ERROR] api_gps_checkin: {e}")
        return jsonify({'ok': False, 'error': str(e)}), 500


@jobs_bp.route('/api/gps/checkout', methods=['POST'])
def api_gps_checkout():
    """Record GPS check-out and create timesheet entry."""
    user, err = require_auth()
    if err:
        return err
    
    try:
        data = request.get_json() or {}
        job_id = data.get('job_id')
        check_in_time = data.get('check_in_time')
        check_out_time = data.get('check_out_time')
        hours_worked = data.get('hours_worked', 0)
        lat = data.get('lat')
        lng = data.get('lng')
        
        db = get_db()
        
        # Update GPS log
        db.execute('''
            UPDATE gps_logs 
            SET check_out_time = ?, check_out_lat = ?, check_out_lng = ?, hours_worked = ?
            WHERE job_id = ? AND user_id = ? AND check_out_time IS NULL
            ORDER BY id DESC LIMIT 1
        ''', [check_out_time, lat, lng, hours_worked, job_id, session.get('user_id')])
        
        # Auto-create timesheet entry
        if hours_worked > 0:
            today = check_out_time.split('T')[0] if check_out_time else None
            db.execute('''
                INSERT INTO timesheets (job_id, employee_id, date, hours, description)
                VALUES (?, ?, ?, ?, ?)
            ''', [job_id, session.get('user_id'), today, round(hours_worked, 2), 'GPS auto-záznam'])
        
        db.commit()
        
        return jsonify({'ok': True, 'hours_logged': round(hours_worked, 2)})
    except Exception as e:
        print(f"[ERROR] api_gps_checkout: {e}")
        return jsonify({'ok': False, 'error': str(e)}), 500


# ============================================================
# CLIENT PORTAL API
# ============================================================

@jobs_bp.route('/portal')
def client_portal():
    """Serve client portal page."""
    return render_template('client-portal.html')


@jobs_bp.route('/api/portal/job')
def api_portal_job():
    """Get job by client code (no auth required)."""
    code = request.args.get('code', '').strip()
    
    if not code:
        return jsonify({'error': 'Code required'}), 400
    
    db = get_db()
    
    # Search by code or client name
    job = db.execute('''
        SELECT * FROM jobs 
        WHERE code = ? OR client LIKE ? OR id = ?
        LIMIT 1
    ''', [code, f'%{code}%', code if code.isdigit() else -1]).fetchone()
    
    if not job:
        return jsonify({'error': 'Job not found'}), 404
    
    job_dict = dict(job)
    
    # Get task stats
    tasks = db.execute('''
        SELECT 
            COUNT(*) as total,
            SUM(CASE WHEN status = 'done' THEN 1 ELSE 0 END) as completed
        FROM tasks WHERE job_id = ?
    ''', [job['id']]).fetchone()
    
    job_dict['tasks_total'] = tasks['total'] or 0
    job_dict['tasks_completed'] = tasks['completed'] or 0
    
    # Calculate progress
    if job_dict['tasks_total'] > 0:
        job_dict['progress'] = int((job_dict['tasks_completed'] / job_dict['tasks_total']) * 100)
    else:
        job_dict['progress'] = job.get('progress', 0) or 0
    
    return jsonify(job_dict)


@jobs_bp.route('/api/portal/job/<int:job_id>/updates')
def api_portal_updates(job_id):
    """Get job updates/timeline for portal."""
    db = get_db()
    
    # Get completed tasks as updates
    tasks = db.execute('''
        SELECT title, 'Úkol dokončen' as description, 
               COALESCE(updated_at, created_at) as date
        FROM tasks 
        WHERE job_id = ? AND status = 'done'
        ORDER BY date DESC
        LIMIT 10
    ''', [job_id]).fetchall()
    
    updates = [{'title': t['title'], 'description': t['description'], 'date': t['date']} for t in tasks]
    
    # Add job notes as updates if available
    job = db.execute('SELECT note, created_at FROM jobs WHERE id = ?', [job_id]).fetchone()
    if job and job['note']:
        updates.insert(0, {
            'title': 'Poznámka k zakázce',
            'description': job['note'][:200],
            'date': job['created_at']
        })
    
    return jsonify(updates)


@jobs_bp.route('/api/portal/job/<int:job_id>/photos')
def api_portal_photos(job_id):
    """Get job photos for portal."""
    db = get_db()
    
    # Check if job_photos table exists
    try:
        photos = db.execute('''
            SELECT url, thumbnail, created_at as date
            FROM job_photos
            WHERE job_id = ?
            ORDER BY created_at DESC
        ''', [job_id]).fetchall()
        
        return jsonify([dict(p) for p in photos])
    except:
        # Table doesn't exist
        return jsonify([])


# ============================================================
# AI ESTIMATE API (for future AI integration)
# ============================================================

@jobs_bp.route('/api/ai/estimate', methods=['POST'])
def api_ai_estimate():
    """Generate AI estimate for a job based on description/photo."""
    user, err = require_auth()
    if err:
        return err
    
    try:
        data = request.get_json() or {}
        description = data.get('description', '')
        photo_base64 = data.get('photo')
        job_type = data.get('type', 'general')
        
        # Simple rule-based estimates (can be replaced with actual AI)
        estimates = {
            'plot': {'days': 3, 'material': 12000, 'price': 35000},
            'zahrada': {'days': 5, 'material': 8000, 'price': 45000},
            'terasa': {'days': 4, 'material': 15000, 'price': 50000},
            'general': {'days': 2, 'material': 5000, 'price': 20000}
        }
        
        # Parse description for keywords
        desc_lower = description.lower()
        estimate_type = 'general'
        
        for keyword in ['plot', 'oplocení', 'plotov']:
            if keyword in desc_lower:
                estimate_type = 'plot'
                break
        for keyword in ['zahrad', 'trávník', 'vysázení']:
            if keyword in desc_lower:
                estimate_type = 'zahrada'
                break
        for keyword in ['teras', 'dlažb', 'dřev']:
            if keyword in desc_lower:
                estimate_type = 'terasa'
                break
        
        # Extract numbers from description (e.g., "50m plot")
        import re
        numbers = re.findall(r'(\d+)\s*m', desc_lower)
        multiplier = 1
        if numbers:
            meters = int(numbers[0])
            multiplier = max(1, meters / 20)  # Base estimate is for ~20m
        
        base = estimates[estimate_type]
        
        result = {
            'type': estimate_type,
            'estimated_days': round(base['days'] * multiplier),
            'estimated_material': round(base['material'] * multiplier),
            'estimated_price': round(base['price'] * multiplier),
            'confidence': 0.7,
            'note': f'Odhad pro typ "{estimate_type}" na základě popisu'
        }
        
        return jsonify(result)
    except Exception as e:
        print(f"[ERROR] api_ai_estimate: {e}")
        return jsonify({'error': str(e)}), 500


# ============================================================
# CREW CONTROL SYSTEM API
# ============================================================



# Additional jobs routes from main.py
@jobs_bp.route("/gd/api/jobs", methods=["GET", "POST", "PATCH", "DELETE"])
def gd_api_jobs():
    return api_jobs()

@jobs_bp.route("/gd/api/jobs/<int:job_id>", methods=["GET"])
def gd_api_job_detail(job_id):
    return api_job_detail(job_id)

# === ATTACHMENTS API ===
import os
import uuid
from werkzeug.utils import secure_filename

UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif', 'doc', 'docx', 'xls', 'xlsx', 'zip', 'mp4', 'mov'}

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

@jobs_bp.route('/api/jobs/<int:job_id>/complete', methods=['GET'])
def get_job_complete(job_id):
    """Získá kompletní informace o zakázce"""
    try:
        db = get_db()
        cursor = db.cursor()
        
        cursor.execute("SELECT * FROM jobs WHERE id = ?", (job_id,))
        job = dict_from_db_row(cursor.fetchone())
        
        if not job:
            return jsonify({"error": "Job not found"}), 404
        
        cursor.execute("SELECT * FROM job_clients WHERE job_id = ?", (job_id,))
        client = dict_from_db_row(cursor.fetchone())
        
        cursor.execute("SELECT * FROM job_locations WHERE job_id = ?", (job_id,))
        location = dict_from_db_row(cursor.fetchone())
        
        cursor.execute("SELECT * FROM job_milestones WHERE job_id = ? ORDER BY order_num, planned_date", (job_id,))
        milestones = [dict_from_db_row(row) for row in cursor.fetchall()]
        
        cursor.execute("SELECT * FROM job_materials WHERE job_id = ?", (job_id,))
        materials = [dict_from_db_row(row) for row in cursor.fetchall()]
        
        cursor.execute("SELECT * FROM job_equipment WHERE job_id = ? ORDER BY date_from", (job_id,))
        equipment = [dict_from_db_row(row) for row in cursor.fetchall()]
        
        cursor.execute("""
            SELECT jta.*, e.name as employee_name, e.position as employee_position
            FROM job_team_assignments jta
            LEFT JOIN employees e ON jta.employee_id = e.id
            WHERE jta.job_id = ? AND jta.is_active = 1
        """, (job_id,))
        team = [dict_from_db_row(row) for row in cursor.fetchall()]
        
        cursor.execute("SELECT * FROM job_subcontractors WHERE job_id = ?", (job_id,))
        subcontractors = [dict_from_db_row(row) for row in cursor.fetchall()]
        
        cursor.execute("SELECT * FROM job_risks WHERE job_id = ? AND status != 'closed'", (job_id,))
        risks = [dict_from_db_row(row) for row in cursor.fetchall()]
        
        cursor.execute("SELECT * FROM job_payments WHERE job_id = ? ORDER BY planned_date", (job_id,))
        payments = [dict_from_db_row(row) for row in cursor.fetchall()]
        
        cursor.execute("SELECT * FROM job_photos WHERE job_id = ? LIMIT 50", (job_id,))
        photos = [dict_from_db_row(row) for row in cursor.fetchall()]
        
        result = {
            "job": job,
            "client": client,
            "location": location,
            "milestones": milestones,
            "materials": materials,
            "equipment": equipment,
            "team": team,
            "subcontractors": subcontractors,
            "risks": risks,
            "payments": payments,
            "photos": photos,
            "summary": {
                "milestones_count": len(milestones),
                "materials_count": len(materials),
                "team_size": len(team),
                "photos_count": len(photos)
            }
        }
        
        return jsonify(result), 200
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@jobs_bp.route('/api/jobs/<int:job_id>/client', methods=['GET', 'POST', 'PUT'])
def manage_job_client(job_id):
    """Správa klienta"""
    db = get_db()
    
    try:
        if request.method == 'GET':
            cursor = db.cursor()
            cursor.execute("SELECT * FROM job_clients WHERE job_id = ?", (job_id,))
            client = dict_from_db_row(cursor.fetchone())
            return jsonify(client if client else {}), 200
            
        elif request.method in ['POST', 'PUT']:
            data = request.get_json()
            
            if not data.get('name'):
                return jsonify({"error": "Name is required"}), 400
            
            cursor = db.cursor()
            cursor.execute("SELECT id FROM job_clients WHERE job_id = ?", (job_id,))
            exists = cursor.fetchone()
            
            if exists:
                db.execute("""
                    UPDATE job_clients SET
                        name = ?, company = ?, ico = ?, dic = ?,
                        email = ?, phone = ?, phone_secondary = ?,
                        billing_street = ?, billing_city = ?, billing_zip = ?
                    WHERE job_id = ?
                """, (
                    data.get('name'), data.get('company'), data.get('ico'), data.get('dic'),
                    data.get('email'), data.get('phone'), data.get('phone_secondary'),
                    data.get('billing_street'), data.get('billing_city'), data.get('billing_zip'),
                    job_id
                ))
            else:
                db.execute("""
                    INSERT INTO job_clients (
                        job_id, name, company, ico, dic, email, phone, 
                        phone_secondary, billing_street, billing_city, billing_zip
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    job_id, data.get('name'), data.get('company'), data.get('ico'), data.get('dic'),
                    data.get('email'), data.get('phone'), data.get('phone_secondary'),
                    data.get('billing_street'), data.get('billing_city'), data.get('billing_zip')
                ))
            
            db.commit()
            return jsonify({"success": True}), 200
            
    except Exception as e:
        db.rollback()
        return jsonify({"error": str(e)}), 500

@jobs_bp.route('/api/jobs/<int:job_id>/location', methods=['GET', 'POST', 'PUT'])
def manage_job_location(job_id):
    """Správa lokace"""
    db = get_db()
    
    try:
        if request.method == 'GET':
            cursor = db.cursor()
            cursor.execute("SELECT * FROM job_locations WHERE job_id = ?", (job_id,))
            location = dict_from_db_row(cursor.fetchone())
            return jsonify(location if location else {}), 200
            
        elif request.method in ['POST', 'PUT']:
            data = request.get_json()
            
            cursor = db.cursor()
            cursor.execute("SELECT id FROM job_locations WHERE job_id = ?", (job_id,))
            exists = cursor.fetchone()
            
            if exists:
                db.execute("""
                    UPDATE job_locations SET
                        street = ?, city = ?, zip = ?, lat = ?, lng = ?,
                        parking = ?, access_notes = ?, gate_code = ?
                    WHERE job_id = ?
                """, (
                    data.get('street'), data.get('city'), data.get('zip'),
                    data.get('lat'), data.get('lng'), data.get('parking'),
                    data.get('access_notes'), data.get('gate_code'), job_id
                ))
            else:
                db.execute("""
                    INSERT INTO job_locations (
                        job_id, street, city, zip, lat, lng,
                        parking, access_notes, gate_code
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    job_id, data.get('street'), data.get('city'), data.get('zip'),
                    data.get('lat'), data.get('lng'), data.get('parking'),
                    data.get('access_notes'), data.get('gate_code')
                ))
            
            db.commit()
            return jsonify({"success": True}), 200
            
    except Exception as e:
        db.rollback()
        return jsonify({"error": str(e)}), 500

@jobs_bp.route('/api/jobs/<int:job_id>/milestones', methods=['GET', 'POST'])
def manage_milestones(job_id):
    """Seznam a vytvoření milníků"""
    db = get_db()
    
    try:
        if request.method == 'GET':
            cursor = db.cursor()
            cursor.execute("SELECT * FROM job_milestones WHERE job_id = ? ORDER BY order_num", (job_id,))
            milestones = [dict_from_db_row(row) for row in cursor.fetchall()]
            return jsonify(milestones), 200
            
        elif request.method == 'POST':
            data = request.get_json()
            
            if not data.get('name'):
                return jsonify({"error": "Name is required"}), 400
            
            cursor = db.cursor()
            cursor.execute("SELECT COALESCE(MAX(order_num), 0) + 1 FROM job_milestones WHERE job_id = ?", (job_id,))
            next_order = cursor.fetchone()[0]
            
            db.execute("""
                INSERT INTO job_milestones (
                    job_id, name, description, planned_date, status, order_num
                ) VALUES (?, ?, ?, ?, ?, ?)
            """, (
                job_id, data.get('name'), data.get('description'),
                data.get('planned_date'), data.get('status', 'pending'), next_order
            ))
            
            db.commit()
            return jsonify({"success": True, "id": db.cursor().lastrowid}), 201
            
    except Exception as e:
        db.rollback()
        return jsonify({"error": str(e)}), 500

@jobs_bp.route('/api/jobs/<int:job_id>/milestones/<int:milestone_id>', methods=['PUT', 'DELETE'])
def manage_milestone(job_id, milestone_id):
    """Update nebo delete milníku"""
    db = get_db()
    
    try:
        if request.method == 'PUT':
            data = request.get_json()
            
            db.execute("""
                UPDATE job_milestones SET
                    name = ?, description = ?, planned_date = ?,
                    actual_date = ?, status = ?, completion_percent = ?
                WHERE id = ? AND job_id = ?
            """, (
                data.get('name'), data.get('description'), data.get('planned_date'),
                data.get('actual_date'), data.get('status'), data.get('completion_percent', 0),
                milestone_id, job_id
            ))
            
            db.commit()
            return jsonify({"success": True}), 200
            
        elif request.method == 'DELETE':
            db.execute("DELETE FROM job_milestones WHERE id = ? AND job_id = ?", (milestone_id, job_id))
            db.commit()
            return jsonify({"success": True}), 200
            
    except Exception as e:
        db.rollback()
        return jsonify({"error": str(e)}), 500

@jobs_bp.route('/api/jobs/<int:job_id>/team', methods=['GET', 'POST'])
def manage_team(job_id):
    """Seznam a přiřazení týmu"""
    db = get_db()
    
    try:
        if request.method == 'GET':
            cursor = db.cursor()
            cursor.execute("""
                SELECT jta.*, e.name as employee_name, e.position as employee_position
                FROM job_team_assignments jta
                LEFT JOIN employees e ON jta.employee_id = e.id
                WHERE jta.job_id = ? AND jta.is_active = 1
            """, (job_id,))
            team = [dict_from_db_row(row) for row in cursor.fetchall()]
            return jsonify({"team": team, "summary": {"size": len(team)}}), 200
            
        elif request.method == 'POST':
            data = request.get_json()
            
            if not data.get('employee_id'):
                return jsonify({"error": "Employee ID is required"}), 400
            
            db.execute("""
                INSERT INTO job_team_assignments (
                    job_id, employee_id, role, hours_planned, hours_actual
                ) VALUES (?, ?, ?, ?, ?)
            """, (
                job_id, data.get('employee_id'), data.get('role', 'worker'),
                data.get('hours_planned', 0), data.get('hours_actual', 0)
            ))
            
            db.commit()
            return jsonify({"success": True}), 201
            
    except Exception as e:
        db.rollback()
        return jsonify({"error": str(e)}), 500

print("✅ Jobs Extended API loaded")

# ----------------- Planning Module API -----------------
# Import planning functions directly
import planning_api

# Make get_db available to planning_api
planning_api.get_db = get_db

# Planning routes
