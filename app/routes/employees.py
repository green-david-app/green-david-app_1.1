# Green David App
from flask import Blueprint, jsonify, request, redirect, send_from_directory, render_template
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash
import sqlite3
from app.database import get_db
from app.utils.permissions import require_auth, require_role, requires_role, get_current_user, normalize_role, normalize_employee_role
from app.utils.helpers import _normalize_date
from app.config import ROLES

employees_bp = Blueprint('employees', __name__)


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def get_active_members_count(db):
    """Počet aktivních zaměstnanců"""
    row = db.execute("SELECT COUNT(*) as cnt FROM employees WHERE status IN ('active', 'Aktivní') OR status IS NULL").fetchone()
    return row['cnt'] if row else 0

def get_average_utilization(db, week_start, week_end):
    """Průměrná vytíženost týmu v daném týdnu (%)"""
    employees = db.execute("SELECT id FROM employees WHERE status IN ('active', 'Aktivní') OR status IS NULL").fetchall()
    if not employees:
        return 0
    total_util = 0
    count = 0
    for emp in employees:
        emp_dict = dict(emp)
        emp_id = emp_dict['id']
        # Získej kapacitu z profilu nebo použij fallback
        profile = db.execute("SELECT weekly_capacity_hours FROM team_member_profile WHERE employee_id = ?", (emp_id,)).fetchone()
        capacity = (dict(profile)['weekly_capacity_hours'] if profile else None) or 40
        worked_row = db.execute(
            "SELECT SUM(COALESCE(duration_minutes, CAST(hours * 60 AS INTEGER))) / 60.0 as total FROM timesheets WHERE employee_id=? AND date >= ? AND date <= ?",
            (emp_id, week_start, week_end)
        ).fetchone()
        worked = (worked_row['total'] or 0) if worked_row else 0
        if capacity > 0:
            total_util += (worked / capacity) * 100
        count += 1
    return round(total_util / count, 1) if count > 0 else 0

def get_overloaded_count(db, week_start, week_end):
    """Počet přetížených zaměstnanců (>100% kapacity)"""
    employees = db.execute("SELECT id FROM employees WHERE status IN ('active', 'Aktivní') OR status IS NULL").fetchall()
    overloaded = 0
    for emp in employees:
        emp_dict = dict(emp)
        emp_id = emp_dict['id']
        # Získej kapacitu z profilu nebo použij fallback
        profile = db.execute("SELECT weekly_capacity_hours FROM team_member_profile WHERE employee_id = ?", (emp_id,)).fetchone()
        capacity = (dict(profile)['weekly_capacity_hours'] if profile else None) or 40
        worked_row = db.execute(
            "SELECT SUM(COALESCE(duration_minutes, CAST(hours * 60 AS INTEGER))) / 60.0 as total FROM timesheets WHERE employee_id=? AND date >= ? AND date <= ?",
            (emp_id, week_start, week_end)
        ).fetchone()
        worked = (worked_row['total'] or 0) if worked_row else 0
        if capacity > 0 and (worked / capacity) > 1.0:
            overloaded += 1
    return overloaded

def get_ai_balance_score(db, week_start, week_end):
    """AI skóre vyváženosti týmu (0-100). Čím rovnoměrnější rozložení, tím vyšší."""
    employees = db.execute("SELECT id FROM employees WHERE status IN ('active', 'Aktivní') OR status IS NULL").fetchall()
    if not employees:
        return 0
    utilizations = []
    for emp in employees:
        emp_dict = dict(emp)
        emp_id = emp_dict['id']
        # Získej kapacitu z profilu nebo použij fallback
        profile = db.execute("SELECT weekly_capacity_hours FROM team_member_profile WHERE employee_id = ?", (emp_id,)).fetchone()
        capacity = (dict(profile)['weekly_capacity_hours'] if profile else None) or 40
        worked_row = db.execute(
            "SELECT SUM(COALESCE(duration_minutes, CAST(hours * 60 AS INTEGER))) / 60.0 as total FROM timesheets WHERE employee_id=? AND date >= ? AND date <= ?",
            (emp_id, week_start, week_end)
        ).fetchone()
        worked = (worked_row['total'] or 0) if worked_row else 0
        utilizations.append((worked / capacity * 100) if capacity > 0 else 0)
    if not utilizations:
        return 0
    avg = sum(utilizations) / len(utilizations)
    if avg == 0:
        return 50  # Neutrální skóre když nikdo nepracoval
    variance = sum((u - avg) ** 2 for u in utilizations) / len(utilizations)
    std_dev = variance ** 0.5
    # Čím nižší odchylka, tím vyšší skóre (max 100)
    score = max(0, min(100, 100 - std_dev))
    return round(score, 0)

def calculate_capacity_percent(profile, current_hours):
    """Vypočítá % vytížení zaměstnance"""
    capacity = profile.get('weekly_capacity_hours', 40) or 40
    if capacity <= 0:
        return 0
    return (current_hours / capacity) * 100

def calculate_capacity_status(percent):
    """Vrátí status na základě % vytížení"""
    if percent > 100:
        return 'overloaded'
    elif percent > 80:
        return 'optimal'
    elif percent > 40:
        return 'available'
    else:
        return 'underutilized'


# --- Team/Employees aliases (to avoid 404) ---
@employees_bp.route("/team")
@employees_bp.route("/team/")
def team_page():
    # Crew Control System - sloučená sekce Tým
    return send_from_directory(".", "team.html")


@employees_bp.route("/employees")
@employees_bp.route("/employees/")
@employees_bp.route("/zamestnanci")
@employees_bp.route("/zamestnanci/")
def employees_redirect():
    # Přesměrování ze starého employees na novou sekci Tým
    return redirect("/team")


@employees_bp.route("/team.html")
def team_html_direct():
    return send_from_directory(".", "team.html")


@employees_bp.route("/admin/roles")
@employees_bp.route("/admin/roles/")
@employees_bp.route("/admin_roles.html")
def admin_roles():
    """Stránka pro správu rolí - pouze pro ownera"""
    u, err = require_auth()
    if err:
        return redirect('/login')
    if u and u.get('role') not in ('owner', 'admin'):
        return jsonify({"ok": False, "error": "forbidden"}), 403
    return render_template("admin_roles.html")


@employees_bp.route("/employees.html")
def employees_html():
    return send_from_directory(".", "employees.html")


@employees_bp.route("/api/employees/<int:emp_id>", methods=["DELETE"])
@requires_role('owner', 'admin', 'manager')
def api_delete_employee(emp_id):
    """Smazání zaměstnance podle ID v URL"""
    user = get_current_user()
    if not user:
        return jsonify({"ok": False, "error": "unauthorized"}), 401
    
    user_role = normalize_role(user.get('role')) or 'owner'
    if user_role not in ('owner', 'admin', 'manager'):
        return jsonify({"ok": False, "error": "forbidden"}), 403
    
    db = get_db()
    try:
        db.execute("DELETE FROM employees WHERE id=?", (emp_id,))
        db.commit()
        print(f"✓ Employee {emp_id} deleted successfully")
        return jsonify({"ok": True})
    except Exception as e:
        db.rollback()
        print(f"✗ Error deleting employee: {e}")
        return jsonify({"ok": False, "error": str(e)}), 500


@employees_bp.route("/api/employees", methods=["GET","POST","PATCH","DELETE"])
@requires_role('owner', 'admin', 'manager', 'lander', 'worker')
def api_employees():
    user = get_current_user()
    if not user:
        return jsonify({"ok": False, "error": "unauthorized"}), 401
    
    db = get_db()
    if request.method == "GET":
        # Všichni přihlášení uživatelé mohou číst seznam zaměstnanců; u každého zaměstnance doplníme informaci o účtu (pokud existuje).
        rows = db.execute("""
            SELECT e.*,
                   u.id   AS account_user_id,
                   u.email AS account_email,
                   u.role AS account_role,
                   u.active AS account_active
            FROM employees e
            LEFT JOIN users u ON u.id = e.user_id
            ORDER BY e.id DESC
        """).fetchall()

        employees = []
        for r in rows:
            emp = dict(r)
            emp_id = emp["id"]

            # Normalizace role zaměstnance (aby UI bylo konzistentní)
            emp["role"] = normalize_employee_role(emp.get("role"))

            # Účet zaměstnance (pokud je navázaný přes employees.user_id)
            emp["has_account"] = emp.get("account_user_id") is not None
            if emp.get("account_role") is not None:
                emp["account_role"] = normalize_role(emp.get("account_role"))
            
            # Vypočítej hodiny tento týden
            today = datetime.now()
            monday = today - timedelta(days=today.weekday())
            week_start = monday.strftime("%Y-%m-%d")
            week_end = (monday + timedelta(days=6)).strftime("%Y-%m-%d")
            
            timesheet_rows = db.execute(
                "SELECT SUM(hours) as total FROM timesheets WHERE employee_id=? AND date >= ? AND date <= ?",
                (emp_id, week_start, week_end)
            ).fetchone()
            emp["hours_week"] = round(timesheet_rows["total"] or 0, 1)
            
            # Spočítej aktivní zakázky (kde je zaměstnanec přiřazen)
            job_rows = db.execute(
                "SELECT COUNT(DISTINCT job_id) as count FROM job_assignments WHERE employee_id=?",
                (emp_id,)
            ).fetchone()
            emp["active_projects"] = job_rows["count"] or 0
            
            # Spočítej dokončené úkoly
            task_rows = db.execute(
                "SELECT COUNT(*) as count FROM tasks WHERE employee_id=? AND status='completed'",
                (emp_id,)
            ).fetchone()
            emp["completed_tasks"] = task_rows["count"] or 0
            
            # Status (online pokud má výkazy za posledních 24h)
            recent_timesheet = db.execute(
                "SELECT COUNT(*) as count FROM timesheets WHERE employee_id=? AND date >= date('now', '-1 day')",
                (emp_id,)
            ).fetchone()
            emp["status"] = "online" if (recent_timesheet["count"] or 0) > 0 else "offline"
            
            # NOVÉ: Rozšířený profil z Crew Control System (pokud existuje)
            try:
                profile = db.execute(
                    "SELECT * FROM team_member_profile WHERE employee_id = ?",
                    (emp_id,)
                ).fetchone()
                
                if profile:
                    profile_dict = dict(profile)
                    # Parse JSON fields
                    import json as json_lib
                    try:
                        profile_dict['skills'] = json_lib.loads(profile_dict.get('skills') or '[]')
                        profile_dict['certifications'] = json_lib.loads(profile_dict.get('certifications') or '[]')
                        profile_dict['preferred_work_types'] = json_lib.loads(profile_dict.get('preferred_work_types') or '[]')
                    except:
                        profile_dict['skills'] = []
                        profile_dict['certifications'] = []
                        profile_dict['preferred_work_types'] = []
                    
                    # Vypočítej kapacitu
                    current_week_hours = emp.get("hours_week", 0)
                    weekly_capacity = profile_dict.get('weekly_capacity_hours', 40.0)
                    capacity_percent = (current_week_hours / weekly_capacity * 100) if weekly_capacity > 0 else 0
                    
                    # Urči status kapacity
                    if capacity_percent > 90:
                        capacity_status = 'overloaded'
                    elif capacity_percent < 50:
                        capacity_status = 'underutilized'
                    else:
                        capacity_status = 'normal'
                    
                    emp["profile"] = {
                        'skills': profile_dict['skills'],
                        'certifications': profile_dict['certifications'],
                        'weekly_capacity_hours': weekly_capacity,
                        'preferred_work_types': profile_dict['preferred_work_types'],
                        'performance_stability_score': profile_dict.get('performance_stability_score', 0.5),
                        'ai_balance_score': profile_dict.get('ai_balance_score', 0.5),
                        'burnout_risk_level': profile_dict.get('burnout_risk_level', 'normal'),
                        'total_jobs_completed': profile_dict.get('total_jobs_completed', 0),
                        'current_active_jobs': profile_dict.get('current_active_jobs', 0),
                        'capacity_percent': round(capacity_percent, 1),
                        'capacity_status': capacity_status
                    }
            except Exception as e:
                # Pokud tabulka ještě neexistuje nebo je chyba, prostě přeskočíme
                pass
            
            employees.append(emp)
        
        return jsonify({"ok": True, "employees": employees})
    if request.method == "POST":
        # Pouze owner a manager mohou přidávat zaměstnance
        user_role = normalize_role(user.get('role')) or 'owner'
        if user_role not in ('owner','admin','manager'):
            return jsonify({"ok": False, "error": "forbidden"}), 403
        try:
            data = request.get_json(force=True, silent=True) or {}
            name = data.get("name")
            if not name: return jsonify({"ok": False, "error":"invalid_input"}), 400
            
            # Get all fields with defaults
            role = normalize_employee_role(data.get("role") or "worker")
            phone = data.get("phone") or ""
            email = data.get("email") or ""
            address = data.get("address") or ""
            birth_date = data.get("birth_date") or None
            contract_type = data.get("contract_type") or "HPP"
            start_date = data.get("start_date") or None
            hourly_rate = data.get("hourly_rate") or None
            salary = data.get("salary") or None
            skills = data.get("skills") or ""
            location = data.get("location") or ""
            status = data.get("status") or "active"
            rating = data.get("rating") or 0
            avatar_url = data.get("avatar_url") or ""

            # Delegace (volitelné)
            delegate_employee_id = data.get("delegate_employee_id")
            approver_delegate_employee_id = data.get("approver_delegate_employee_id")
            
            # Build INSERT query with all available columns
            cols = [r[1] for r in db.execute("PRAGMA table_info(employees)").fetchall()]
            insert_cols = ["name", "role"]
            insert_vals = [name, role]
            
            for col in ["phone", "email", "address", "birth_date", "contract_type", "start_date", 
                       "hourly_rate", "salary", "skills", "location", "status", "rating", "avatar_url",
                       "delegate_employee_id", "approver_delegate_employee_id"]:
                if col in cols:
                    insert_cols.append(col)
                    if col == "hourly_rate" or col == "salary" or col == "rating":
                        insert_vals.append(hourly_rate if col == "hourly_rate" else (salary if col == "salary" else rating))
                    else:
                        val = locals().get(col, "")
                        insert_vals.append(val if val else None)
            
            placeholders = ",".join(["?"] * len(insert_vals))
            db.execute(f"INSERT INTO employees({','.join(insert_cols)}) VALUES ({placeholders})", insert_vals)
            db.commit()
            print(f"✓ Employee '{name}' created successfully")
            return jsonify({"ok": True})
        except Exception as e:
            db.rollback()
            print(f"✗ Error creating employee: {e}")
            return jsonify({"ok": False, "error": str(e)}), 500
    if request.method == "PATCH":
        # Pouze owner a manager mohou upravovat zaměstnance
        user_role = normalize_role(user.get('role')) or 'owner'
        if user_role not in ('owner','admin','manager'):
            return jsonify({"ok": False, "error": "forbidden"}), 403
        try:
            data = request.get_json(force=True, silent=True) or {}
            eid = data.get("id") or request.args.get("id", type=int)
            if not eid: return jsonify({"ok": False, "error":"missing_id"}), 400
            updates = []
            params = []
            # Get all available columns from schema
            cols = [r[1] for r in db.execute("PRAGMA table_info(employees)").fetchall()]
            allowed = ["name", "role", "phone", "email", "address", "birth_date", "contract_type", 
                      "start_date", "hourly_rate", "salary", "skills", "location", "status", "rating", "avatar_url",
                      "delegate_employee_id", "approver_delegate_employee_id"]
            for k in allowed:
                if k in data and k in cols:
                    updates.append(f"{k}=?")
                    # Handle numeric fields
                    if k in ["hourly_rate", "salary", "rating"]:
                        params.append(float(data[k]) if data[k] is not None else None)
                    elif k == "role":
                        params.append(normalize_employee_role(data[k]))
                    else:
                        params.append(data[k] if data[k] is not None else "")
            if not updates: return jsonify({"ok": False, "error":"no_updates"}), 400
            params.append(eid)
            db.execute(f"UPDATE employees SET {', '.join(updates)} WHERE id=?", tuple(params))
            db.commit()
            print(f"✓ Employee {eid} updated successfully")
            return jsonify({"ok": True})
        except Exception as e:
            db.rollback()
            print(f"✗ Error updating employee: {e}")
            return jsonify({"ok": False, "error": str(e)}), 500
    if request.method == "DELETE":
        # Pouze owner a manager mohou mazat zaměstnance
        user_role = normalize_role(user.get('role')) or 'owner'
        if user_role not in ('owner','admin','manager'):
            return jsonify({"ok": False, "error": "forbidden"}), 403
        try:
            eid = request.args.get("id", type=int)
            if not eid: return jsonify({"ok": False, "error":"missing_id"}), 400
            db.execute("DELETE FROM employees WHERE id=?", (eid,))
            db.commit()
            print(f"✓ Employee {eid} deleted successfully")
            return jsonify({"ok": True})
        except Exception as e:
            db.rollback()
            print(f"✗ Error deleting employee: {e}")
            return jsonify({"ok": False, "error": str(e)}), 500


# ----------------- Users management API (system users) -----------------
@employees_bp.route("/api/users", methods=["GET"])
@requires_role('owner', 'admin', 'manager', 'lander')
def api_get_users():
    """Seznam uživatelů systému - filtrovaný podle role"""
    user = get_current_user()
    if not user:
        return jsonify({"ok": False, "error": "unauthorized"}), 401
    
    db = get_db()
    
    if user['role'] in ('owner', 'admin', 'manager'):
        # Owner a Manager vidí všechny uživatele
        rows = db.execute("""
            SELECT u.id, u.email, u.name, u.role, u.manager_id, u.active,
                   m.name AS manager_name
            FROM users u
            LEFT JOIN users m ON m.id = u.manager_id
            ORDER BY u.name
        """).fetchall()
    elif normalize_role(user.get('role')) == 'lander':
        # Team lead vidí jen své podřízené
        rows = db.execute("""
            SELECT u.id, u.email, u.name, u.role, u.manager_id, u.active,
                   m.name AS manager_name
            FROM users u
            LEFT JOIN users m ON m.id = u.manager_id
            WHERE u.manager_id = ?
            ORDER BY u.name
        """, (user['id'],)).fetchall()
    else:
        return jsonify({"ok": False, "error": "forbidden"}), 403
    
    users = [dict(r) for r in rows]
    return jsonify({"ok": True, "users": users})


@employees_bp.route("/api/users", methods=["POST"])
@requires_role('owner','admin', 'manager')
def api_add_user():
    """Přidání nového uživatele - jen owner a manager"""
    user = get_current_user()
    if not user:
        return jsonify({"ok": False, "error": "unauthorized"}), 401
    
    data = request.get_json(force=True, silent=True) or {}
    name = data.get("name", "").strip()
    email = data.get("email", "").strip().lower()
    password = data.get("password", "")
    role = normalize_role(data.get("role", "worker"))
    manager_id = data.get("manager_id")
    employee_id = data.get("employee_id")
    
    if not name or not email or not password:
        return jsonify({"ok": False, "error": "missing_fields"}), 400
    
    if normalize_role(role) not in ROLES:
        return jsonify({"ok": False, "error": "invalid_role"}), 400
    
    # Manager nemůže vytvořit owner/admin účty
    if normalize_role(user.get('role')) not in ('owner','admin') and role in ('owner','admin'):
        return jsonify({"ok": False, "error": "forbidden"}), 403
    
    # Pokud není zadán manager_id, použije se aktuální uživatel jako manager
    if manager_id is None:
        manager_id = user['id']
    
    db = get_db()
    try:
        db.execute(
            "INSERT INTO users (name, email, role, password_hash, manager_id, active) VALUES (?, ?, ?, ?, ?, 1)",
            (name, email, role, generate_password_hash(password, method='pbkdf2:sha256'), manager_id)
        )
        db.commit()
        new_id = db.execute("SELECT last_insert_rowid()").fetchone()[0]

        # Volitelné navázání účtu na zaměstnance (employees.user_id)
        if employee_id is not None:
            try:
                db.execute("UPDATE employees SET user_id = ? WHERE id = ?", (new_id, int(employee_id)))
                db.commit()
            except Exception:
                db.rollback()
        return jsonify({"ok": True, "id": new_id})
    except sqlite3.IntegrityError:
        db.rollback()
        return jsonify({"ok": False, "error": "email_exists"}), 400
    except Exception as e:
        db.rollback()
        return jsonify({"ok": False, "error": str(e)}), 500


@employees_bp.route("/api/users/unlinked", methods=["GET"])
@requires_role('owner', 'admin')
def api_unlinked_users():
    """Vrátí všechny uživatele s info o propojení"""
    db = get_db()
    rows = db.execute("""
        SELECT u.id, u.name, u.email, u.role, u.active,
               e.id AS linked_employee_id,
               e.name AS linked_employee_name
        FROM users u 
        LEFT JOIN employees e ON e.user_id = u.id
        WHERE u.active = 1
        ORDER BY u.name
    """).fetchall()
    users = []
    for r in rows:
        d = dict(r)
        d['is_linked'] = d.get('linked_employee_id') is not None
        users.append(d)
    return jsonify({"ok": True, "users": users})

@employees_bp.route("/api/employees/<int:emp_id>/link-account", methods=["POST"])
@requires_role('owner', 'admin')
def api_link_account(emp_id):
    """Propojí zaměstnance s existujícím user účtem (přepíše předchozí propojení)"""
    data = request.get_json(force=True, silent=True) or {}
    user_id = data.get('user_id')
    if not user_id:
        return jsonify({"ok": False, "error": "missing_user_id"}), 400
    db = get_db()
    try:
        user = db.execute("SELECT id FROM users WHERE id = ?", (user_id,)).fetchone()
        if not user:
            return jsonify({"ok": False, "error": "user_not_found"}), 404
        emp = db.execute("SELECT id FROM employees WHERE id = ?", (emp_id,)).fetchone()
        if not emp:
            return jsonify({"ok": False, "error": "employee_not_found"}), 404
        # Odpoj tento user účet od jiného zaměstnance (pokud byl propojený jinde)
        db.execute("UPDATE employees SET user_id = NULL WHERE user_id = ?", (user_id,))
        # Propoj s tímto zaměstnancem
        db.execute("UPDATE employees SET user_id = ? WHERE id = ?", (user_id, emp_id))
        db.commit()
        print(f"✓ Employee {emp_id} linked to user {user_id}")
        return jsonify({"ok": True})
    except Exception as e:
        db.rollback()
        print(f"✗ Error linking account: {e}")
        return jsonify({"ok": False, "error": str(e)}), 500

@employees_bp.route("/api/employees/<int:emp_id>/unlink-account", methods=["POST"])
@requires_role('owner', 'admin')
def api_unlink_account(emp_id):
    """Odpojí přihlašovací účet od zaměstnance"""
    db = get_db()
    try:
        db.execute("UPDATE employees SET user_id = NULL WHERE id = ?", (emp_id,))
        db.commit()
        print(f"✓ Employee {emp_id} unlinked from user account")
        return jsonify({"ok": True})
    except Exception as e:
        db.rollback()
        return jsonify({"ok": False, "error": str(e)}), 500

@employees_bp.route("/api/users/<int:user_id>", methods=["DELETE"])
@requires_role('owner')
def api_delete_user(user_id):
    """Smazání/deaktivace user účtu - pouze owner"""
    user = get_current_user()
    # Nelze smazat sám sebe
    if user and user['id'] == user_id:
        return jsonify({"ok": False, "error": "Nemůžete smazat vlastní účet"}), 400
    db = get_db()
    try:
        # Odpoj od zaměstnance
        db.execute("UPDATE employees SET user_id = NULL WHERE user_id = ?", (user_id,))
        # Deaktivuj účet (soft delete)
        db.execute("UPDATE users SET active = 0 WHERE id = ?", (user_id,))
        db.commit()
        print(f"✓ User {user_id} deactivated")
        return jsonify({"ok": True})
    except Exception as e:
        db.rollback()
        return jsonify({"ok": False, "error": str(e)}), 500

@employees_bp.route("/api/users/<int:user_id>/role", methods=["PUT"])
@requires_role('owner','admin')
def api_change_user_role(user_id):
    """Změna role uživatele - jen owner"""
    data = request.get_json(force=True, silent=True) or {}
    new_role = normalize_role(data.get("role"))

    if new_role not in ROLES:
        return jsonify({"ok": False, "error": "invalid_role"}), 400
    
    db = get_db()
    try:
        db.execute("UPDATE users SET role = ? WHERE id = ?", (new_role, user_id))
        db.commit()
        return jsonify({"ok": True})
    except Exception as e:
        db.rollback()
        return jsonify({"ok": False, "error": str(e)}), 500

# Additional routes from main.py
@employees_bp.route("/gd/api/trainings", methods=["GET"])
def gd_api_trainings_get():
    """Seznam školení s filtry"""
    u, err = require_role(write=False)
    if err:
        return err
    db = get_db()
    
    try:
        import json as json_lib
        
        # Filtry
        d_from = _normalize_date(request.args.get("from"))
        d_to = _normalize_date(request.args.get("to"))
        category = request.args.get("category")
        is_paid = request.args.get("is_paid")
        employee_id = request.args.get("employee_id", type=int)
        
        # Build query
        conds = []
        params = []
        
        if d_from:
            conds.append("date(t.date_start) >= date(?)")
            params.append(d_from)
        if d_to:
            conds.append("date(t.date_start) <= date(?)")
            params.append(d_to)
        if category:
            conds.append("t.category = ?")
            params.append(category)
        if is_paid is not None:
            conds.append("t.is_paid = ?")
            params.append(1 if is_paid == 'true' else 0)
        if employee_id:
            conds.append("EXISTS (SELECT 1 FROM training_attendees ta WHERE ta.training_id = t.id AND ta.employee_id = ?)")
            params.append(employee_id)
        
        where_clause = " WHERE " + " AND ".join(conds) if conds else ""
        
        # Get trainings
        trainings = db.execute(f"""
            SELECT t.*, 
                   COUNT(DISTINCT ta.id) as attendees_count,
                   COUNT(DISTINCT CASE WHEN ta.status = 'completed' THEN ta.id END) as completed_count
            FROM trainings t
            LEFT JOIN training_attendees ta ON ta.training_id = t.id
            {where_clause}
            GROUP BY t.id
            ORDER BY t.date_start DESC, t.id DESC
        """, params).fetchall()
        
        # Parse JSON fields
        result = []
        for t in trainings:
            training_dict = dict(t)
            # Parse JSON fields
            if training_dict.get('skills_gained'):
                try:
                    training_dict['skills_gained'] = json_lib.loads(training_dict['skills_gained'])
                except:
                    training_dict['skills_gained'] = []
            else:
                training_dict['skills_gained'] = []
            
            result.append(training_dict)
        
        return jsonify({"ok": True, "trainings": result, "total": len(result)})
    except Exception as e:
        print(f"✗ Error getting trainings: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"ok": False, "error": "server_error", "message": str(e)}), 500


def calculate_training_cost(cost_data, db):
    """Vypočítá náklady na školení: přímé náklady, mzdové náklady, opportunity cost"""
    # Přímé náklady
    direct_costs = (
        float(cost_data.get('cost_training') or 0) +
        float(cost_data.get('cost_travel') or 0) +
        float(cost_data.get('cost_accommodation') or 0) +
        float(cost_data.get('cost_meals') or 0) +
        float(cost_data.get('cost_other') or 0)
    )
    
    # Mzdové náklady
    wage_cost = 0
    opportunity_cost = 0
    compensation_type = cost_data.get('compensation_type', 'paid_workday')
    duration_hours = float(cost_data.get('duration_hours') or 8)
    attendee_count = int(cost_data.get('attendee_count') or 0)
    
    if compensation_type == 'paid_workday' and attendee_count > 0:
        wage_per_person = cost_data.get('wage_cost_per_person')
        if wage_per_person:
            wage_cost = float(wage_per_person) * attendee_count
        else:
            # Odhadni z průměrné hodinové sazby zaměstnanců
            try:
                avg_rate = db.execute(
                    "SELECT AVG(COALESCE(hourly_rate, 250)) FROM employees WHERE active = 1"
                ).fetchone()[0] or 250
                wage_cost = avg_rate * duration_hours * attendee_count
            except:
                wage_cost = 250 * duration_hours * attendee_count
        
        # Opportunity cost = ušlý zisk z práce
        opportunity_cost = wage_cost * 0.3  # ~30% marže
    
    return direct_costs, wage_cost, opportunity_cost


@employees_bp.route("/gd/api/trainings", methods=["POST"])
def gd_api_trainings_post():
    """Vytvoření nového školení"""
    u, err = require_role(write=True)
    if err:
        return err
    db = get_db()
    
    try:
        import json as json_lib
        data = request.get_json(force=True, silent=True) or {}
        
        # Validate required fields - podporuj title i name
        training_name = data.get('title') or data.get('name')
        if not training_name or not data.get('date_start'):
            return jsonify({"ok": False, "error": "missing_required_fields", "message": "Chybí název nebo datum školení"}), 400
        
        # Calculate costs
        # Podporuj různé formáty účastníků
        participants_raw = data.get('participants') or data.get('attendees') or data.get('attendee_ids') or '[]'
        if isinstance(participants_raw, str):
            try:
                attendee_ids = json_lib.loads(participants_raw)
            except:
                attendee_ids = []
        elif isinstance(participants_raw, list):
            attendee_ids = participants_raw
        else:
            attendee_ids = []
        attendee_count = len(attendee_ids)
        compensation_type = data.get('compensation_type', 'paid_workday')
        
        cost_data = {
            'cost_training': data.get('cost_training', 0),
            'cost_travel': data.get('cost_travel', 0),
            'cost_accommodation': data.get('cost_accommodation', 0),
            'cost_meals': data.get('cost_meals', 0),
            'cost_other': data.get('cost_other', 0),
            'duration_hours': data.get('duration_hours'),
            'attendee_count': attendee_count,
            'compensation_type': compensation_type,
            'wage_cost_per_person': data.get('wage_cost_per_person')
        }
        
        direct_costs, wage_cost, opportunity_cost = calculate_training_cost(cost_data, db)
        cost_total = direct_costs + wage_cost
        
        # Prepare skills_gained - podporuj skills_improved i skills_gained
        skills_raw = data.get('skills_improved') or data.get('skills_gained') or '[]'
        if isinstance(skills_raw, str):
            try:
                skills_list = json_lib.loads(skills_raw)
            except:
                skills_list = []
        elif isinstance(skills_raw, list):
            skills_list = skills_raw
        else:
            skills_list = []
        skills_gained_json = json_lib.dumps(skills_list)
        
        # Prepare participants JSON
        participants_json = json_lib.dumps(attendee_ids)
        
        # Dynamicky sestavit INSERT podle dostupných sloupců
        existing_cols = {r[1] for r in db.execute("PRAGMA table_info(trainings)").fetchall()}
        
        date_value = _normalize_date(data.get('date_start') or data.get('date'))
        date_end_value = _normalize_date(data.get('date_end')) if data.get('date_end') else None
        
        days_of_week_raw = data.get('days_of_week', '[0,1,2,3,4,5,6]')
        if isinstance(days_of_week_raw, list):
            days_of_week_json = json_lib.dumps(days_of_week_raw)
        else:
            days_of_week_json = days_of_week_raw if isinstance(days_of_week_raw, str) else '[0,1,2,3,4,5,6]'
        
        col_val_map = {
            'name': training_name,
            'title': data.get('title') or training_name,
            'description': data.get('description'),
            'training_type': data.get('training_type', 'external'),
            'category': data.get('category'),
            'provider': data.get('provider'),
            'provider_type': data.get('provider_type'),
            'date_start': date_value,
            'date': date_value,
            'date_end': date_end_value,
            'days_of_week': days_of_week_json,
            'duration_hours': data.get('duration_hours'),
            'is_paid': 1 if data.get('is_paid', True) else 0,
            'cost_training': data.get('cost_training', 0),
            'cost_travel': data.get('cost_travel', 0),
            'cost_accommodation': data.get('cost_accommodation', 0),
            'cost_meals': data.get('cost_meals', 0),
            'cost_other': data.get('cost_other', 0),
            'cost_total': cost_total,
            'cost_opportunity': opportunity_cost,
            'compensation_type': compensation_type,
            'wage_cost': wage_cost,
            'wage_cost_per_person': data.get('wage_cost_per_person'),
            'location': data.get('location'),
            'is_remote': 1 if data.get('is_remote', False) else 0,
            'has_certificate': 1 if data.get('has_certificate', False) else 0,
            'certificate_name': data.get('certificate_name'),
            'certificate_valid_until': _normalize_date(data.get('certificate_valid_until')) if data.get('certificate_valid_until') else None,
            'skills_gained': skills_gained_json,
            'skills_improved': skills_gained_json,
            'skill_level_increase': data.get('skill_level_increase') or data.get('skill_increase') or 1,
            'skill_increase': data.get('skill_level_increase') or data.get('skill_increase') or 1,
            'participants': participants_json,
            'notes': data.get('notes'),
            'created_by': u['id'] if u else None,
        }
        
        # Filtruj jen sloupce, které existují v tabulce
        insert_cols = []
        insert_vals = []
        for col, val in col_val_map.items():
            if col in existing_cols:
                insert_cols.append(col)
                insert_vals.append(val)
        
        placeholders = ", ".join(["?"] * len(insert_cols))
        sql = f"INSERT INTO trainings ({', '.join(insert_cols)}) VALUES ({placeholders})"
        training_id = db.execute(sql, insert_vals).lastrowid
        
        # Add attendees
        for emp_id in attendee_ids:
            db.execute("""
                INSERT INTO training_attendees (training_id, employee_id, status)
                VALUES (?, ?, 'registered')
            """, (training_id, emp_id))
        
        db.commit()
        
        return jsonify({"ok": True, "id": training_id, "message": "Školení vytvořeno", "success": True})
    except Exception as e:
        db.rollback()
        print(f"✗ Error creating training: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"ok": False, "error": "server_error", "message": str(e)}), 500

@employees_bp.route("/gd/api/trainings/<int:training_id>", methods=["PUT"])
def gd_api_trainings_put(training_id):
    """Úprava školení"""
    u, err = require_role(write=True)
    if err:
        return err
    db = get_db()
    
    try:
        import json as json_lib
        data = request.get_json(force=True, silent=True) or {}
        
        # Check if training exists
        training = db.execute("SELECT id FROM trainings WHERE id = ?", (training_id,)).fetchone()
        if not training:
            return jsonify({"ok": False, "error": "not_found"}), 404
        
        existing_cols = {r[1] for r in db.execute("PRAGMA table_info(trainings)").fetchall()}
        
        # Build UPDATE query
        updates = []
        params = []
        
        allowed_fields = {
            'name': str, 'title': str, 'description': str, 'training_type': str, 'category': str,
            'provider': str, 'provider_type': str, 'duration_hours': float,
            'is_paid': bool, 'cost_training': float, 'cost_travel': float,
            'cost_accommodation': float, 'cost_meals': float, 'cost_other': float,
            'location': str, 'is_remote': bool, 'has_certificate': bool,
            'certificate_name': str, 'rating': int, 'notes': str,
            'skill_level_increase': int, 'skill_increase': int,
            'compensation_type': str, 'wage_cost_per_person': float,
            'days_of_week': str
        }
        
        for field, field_type in allowed_fields.items():
            if field in data and field in existing_cols:
                if field_type == bool:
                    updates.append(f"{field} = ?")
                    params.append(1 if data[field] else 0)
                else:
                    updates.append(f"{field} = ?")
                    params.append(data[field])
        
        # Handle date fields
        for date_field in ['date_start', 'date', 'date_end', 'certificate_valid_until']:
            if date_field in data and date_field in existing_cols:
                updates.append(f"{date_field} = ?")
                params.append(_normalize_date(data[date_field]) if data[date_field] else None)
        
        # Handle skills_gained / skills_improved
        if 'skills_gained' in data or 'skills_improved' in data:
            skills_raw = data.get('skills_gained') or data.get('skills_improved')
            if isinstance(skills_raw, list):
                skills_json = json_lib.dumps(skills_raw)
            elif isinstance(skills_raw, str):
                skills_json = skills_raw
            else:
                skills_json = '[]'
            if 'skills_gained' in existing_cols:
                updates.append("skills_gained = ?"); params.append(skills_json)
            if 'skills_improved' in existing_cols:
                updates.append("skills_improved = ?"); params.append(skills_json)
        
        # Handle participants
        if 'participants' in data:
            participants_raw = data.get('participants')
            if isinstance(participants_raw, str):
                try:
                    attendee_ids = json_lib.loads(participants_raw)
                except:
                    attendee_ids = []
            elif isinstance(participants_raw, list):
                attendee_ids = participants_raw
            else:
                attendee_ids = []
            
            if 'participants' in existing_cols:
                updates.append("participants = ?")
                params.append(json_lib.dumps(attendee_ids))
            
            # Aktualizovat training_attendees
            db.execute("DELETE FROM training_attendees WHERE training_id = ?", (training_id,))
            for emp_id in attendee_ids:
                db.execute("""
                    INSERT INTO training_attendees (training_id, employee_id, status)
                    VALUES (?, ?, 'registered')
                """, (training_id, emp_id))
        
        # Recalculate costs
        if any(field in data for field in ['cost_training', 'cost_travel', 'cost_accommodation', 
                                          'cost_meals', 'cost_other', 'duration_hours', 'compensation_type', 'wage_cost_per_person']):
            # Get current attendee count
            attendee_count = db.execute(
                "SELECT COUNT(*) FROM training_attendees WHERE training_id = ?",
                (training_id,)
            ).fetchone()[0] or 0
            
            # Get current compensation_type if not in update
            current_training = db.execute(
                "SELECT compensation_type, wage_cost_per_person FROM trainings WHERE id = ?",
                (training_id,)
            ).fetchone()
            
            compensation_type = data.get('compensation_type') or (current_training['compensation_type'] if current_training else 'paid_workday')
            wage_cost_per_person = data.get('wage_cost_per_person') or (current_training['wage_cost_per_person'] if current_training else None)
            
            cost_data = {
                'cost_training': data.get('cost_training') or 0,
                'cost_travel': data.get('cost_travel') or 0,
                'cost_accommodation': data.get('cost_accommodation') or 0,
                'cost_meals': data.get('cost_meals') or 0,
                'cost_other': data.get('cost_other') or 0,
                'duration_hours': data.get('duration_hours'),
                'attendee_count': attendee_count,
                'compensation_type': compensation_type,
                'wage_cost_per_person': wage_cost_per_person
            }
            
            direct_costs, wage_cost, opportunity_cost = calculate_training_cost(cost_data, db)
            updates.append("cost_total = ?")
            params.append(direct_costs + wage_cost)
            updates.append("cost_opportunity = ?")
            params.append(opportunity_cost)
            updates.append("wage_cost = ?")
            params.append(wage_cost)
        
        if not updates:
            return jsonify({"ok": False, "error": "no_fields"}), 400
        
        params.append(training_id)
        db.execute(f"UPDATE trainings SET {', '.join(updates)} WHERE id = ?", params)
        db.commit()
        
        return jsonify({"ok": True, "success": True})
    except Exception as e:
        db.rollback()
        print(f"✗ Error updating training: {e}")
        return jsonify({"ok": False, "error": "server_error", "message": str(e)}), 500

@employees_bp.route("/gd/api/trainings/<int:training_id>", methods=["DELETE"])
def gd_api_trainings_delete(training_id):
    """Smazání školení"""
    u, err = require_role(write=True)
    if err:
        return err
    db = get_db()
    
    try:
        # Check if training exists
        training = db.execute("SELECT id FROM trainings WHERE id = ?", (training_id,)).fetchone()
        if not training:
            return jsonify({"ok": False, "error": "not_found"}), 404
        
        # Delete (CASCADE will delete attendees)
        db.execute("DELETE FROM trainings WHERE id = ?", (training_id,))
        db.commit()
        
        return jsonify({"ok": True, "success": True})
    except Exception as e:
        db.rollback()
        print(f"✗ Error deleting training: {e}")
        return jsonify({"ok": False, "error": "server_error", "message": str(e)}), 500

@employees_bp.route("/gd/api/trainings/<int:training_id>/complete", methods=["POST"])
def gd_api_trainings_complete(training_id):
    """Označení školení jako dokončeného + aktualizace skills"""
    u, err = require_role(write=True)
    if err:
        return err
    db = get_db()
    
    try:
        import json as json_lib
        data = request.get_json(force=True, silent=True) or {}
        
        # Check if training exists
        training = db.execute("SELECT id FROM trainings WHERE id = ?", (training_id,)).fetchone()
        if not training:
            return jsonify({"ok": False, "error": "not_found"}), 404
        
        # Update attendees
        attendees_data = data.get('attendees', [])
        for attendee_data in attendees_data:
            employee_id = attendee_data.get('employee_id')
            if not employee_id:
                continue
            
            db.execute("""
                UPDATE training_attendees
                SET status = 'completed',
                    attendance_confirmed = 1,
                    test_score = ?,
                    certificate_issued = ?,
                    personal_rating = ?
                WHERE training_id = ? AND employee_id = ?
            """, (
                attendee_data.get('test_score'),
                1 if attendee_data.get('certificate_issued', False) else 0,
                attendee_data.get('personal_rating'),
                training_id,
                employee_id
            ))
        
        db.commit()
        
        # Update employee skills
        update_employee_skills_from_training(training_id, db)
        
        return jsonify({"ok": True, "success": True})
    except Exception as e:
        db.rollback()
        print(f"✗ Error completing training: {e}")
        return jsonify({"ok": False, "error": "server_error", "message": str(e)}), 500

# ----------------- Trainings Statistics API -----------------
@employees_bp.route("/gd/api/trainings/stats", methods=["GET"])
def gd_api_trainings_stats():
    """Statistiky školení"""
    u, err = require_role(write=False)
    if err:
        return err
    db = get_db()
    
    try:
        from datetime import datetime, timedelta
        
        # Filtry
        date_from = _normalize_date(request.args.get('from'))
        date_to = _normalize_date(request.args.get('to'))
        employee_id = request.args.get('employee_id', type=int)
        
        # Default: poslední rok
        if not date_from or not date_to:
            today = datetime.now().date()
            date_to = today.strftime('%Y-%m-%d')
            date_from = (today - timedelta(days=365)).strftime('%Y-%m-%d')
        
        # Build query
        conds = ["date(t.date_start) >= date(?)", "date(t.date_start) <= date(?)"]
        params = [date_from, date_to]
        
        if employee_id:
            conds.append("EXISTS (SELECT 1 FROM training_attendees ta WHERE ta.training_id = t.id AND ta.employee_id = ?)")
            params.append(employee_id)
        
        where_clause = " WHERE " + " AND ".join(conds)
        
        # Get trainings
        trainings = db.execute(f"""
            SELECT t.*, COUNT(DISTINCT ta.id) as attendees_count
            FROM trainings t
            LEFT JOIN training_attendees ta ON ta.training_id = t.id
            {where_clause}
            GROUP BY t.id
        """, params).fetchall()
        
        # Agregace - přístup pomocí indexů nebo dict() konverze
        total_trainings = len(trainings)
        total_cost = 0
        total_hours = 0
        total_attendees = 0
        paid_trainings = 0
        
        # Konverze Row na dict pro snadnější přístup
        trainings_dicts = []
        for t in trainings:
            t_dict = dict(t) if hasattr(t, 'keys') else t
            trainings_dicts.append(t_dict)
            total_cost += float(t_dict.get('cost_total') or t_dict.get('cost_total', 0) or 0)
            total_hours += float(t_dict.get('duration_hours') or t_dict.get('duration_hours', 0) or 0)
            total_attendees += int(t_dict.get('attendees_count') or t_dict.get('attendees_count', 0) or 0)
            if t_dict.get('is_paid') or (isinstance(t_dict.get('is_paid'), int) and t_dict.get('is_paid') == 1):
                paid_trainings += 1
        
        free_trainings = total_trainings - paid_trainings
        
        # By category
        by_category = {}
        for t_dict in trainings_dicts:
            cat = t_dict.get('category') or 'other'
            if cat not in by_category:
                by_category[cat] = {'count': 0, 'cost': 0, 'hours': 0}
            by_category[cat]['count'] += 1
            by_category[cat]['cost'] += float(t_dict.get('cost_total') or 0)
            by_category[cat]['hours'] += float(t_dict.get('duration_hours') or 0)
        
        # By compensation type
        by_compensation = {
            'paid_workday': {
                'count': 0,
                'total_cost': 0,
                'wage_cost': 0
            },
            'costs_only': {
                'count': 0,
                'total_cost': 0
            },
            'unpaid': {
                'count': 0
            }
        }
        
        for t_dict in trainings_dicts:
            # Bezpečný přístup k compensation_type
            comp_type = dict(t_dict).get('compensation_type') if hasattr(t_dict, 'keys') else (t_dict.get('compensation_type') if isinstance(t_dict, dict) else 'paid_workday')
            comp_type = comp_type or 'paid_workday'
            if comp_type not in by_compensation:
                comp_type = 'paid_workday'
            
            by_compensation[comp_type]['count'] += 1
            if comp_type != 'unpaid':
                cost_total_val = dict(t_dict).get('cost_total') if hasattr(t_dict, 'keys') else (t_dict.get('cost_total') if isinstance(t_dict, dict) else 0)
                by_compensation[comp_type]['total_cost'] += float(cost_total_val or 0)
            if comp_type == 'paid_workday':
                wage_cost_val = dict(t_dict).get('wage_cost') if hasattr(t_dict, 'keys') else (t_dict.get('wage_cost') if isinstance(t_dict, dict) else 0)
                by_compensation[comp_type]['wage_cost'] += float(wage_cost_val or 0)
        
        # ROI odhad (zjednodušený)
        # Předpoklad: 1 hodina školení = 0.5% zvýšení produktivity na 6 měsíců
        # Průměrná měsíční produktivita zaměstnance = 150 000 Kč
        estimated_productivity_gain = total_hours * 0.005 * 150000 * 6 * (total_attendees / max(total_trainings, 1))
        roi_percentage = ((estimated_productivity_gain - total_cost) / max(total_cost, 1)) * 100 if total_cost > 0 else 0
        
        return jsonify({
            "ok": True,
            "stats": {
                "count": total_trainings,
                "total_cost": round(total_cost, 2),
                "total_hours": round(total_hours, 1),
                "attendees": total_attendees,
                "roi_percentage": round(roi_percentage, 1),
                "roi_gain": round(estimated_productivity_gain, 2),
                "payback_months": round(total_cost / max(estimated_productivity_gain / 6, 1), 1) if estimated_productivity_gain > 0 else None
            },
            "period": {"from": date_from, "to": date_to},
            "summary": {
                "total_trainings": total_trainings,
                "paid_trainings": paid_trainings,
                "free_trainings": free_trainings,
                "total_cost": round(total_cost, 2),
                "total_hours": round(total_hours, 1),
                "total_attendees": total_attendees,
                "avg_cost_per_training": round(total_cost / max(total_trainings, 1), 2),
                "avg_cost_per_hour": round(total_cost / max(total_hours, 1), 2),
                "avg_cost_per_attendee": round(total_cost / max(total_attendees, 1), 2)
            },
            "by_category": by_category,
            "by_compensation": by_compensation,
            "roi": {
                "estimated_productivity_gain": round(estimated_productivity_gain, 2),
                "roi_percentage": round(roi_percentage, 1),
                "payback_months": round(total_cost / max(estimated_productivity_gain / 6, 1), 1) if estimated_productivity_gain > 0 else None
            }
        })
    except Exception as e:
        print(f"✗ Error getting training stats: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"ok": False, "error": "server_error", "message": str(e)}), 500

@employees_bp.route("/gd/api/trainings/team-skills", methods=["GET"])
def gd_api_trainings_team_skills():
    """Přehled skills celého týmu"""
    u, err = require_role(write=False)
    if err:
        return err
    db = get_db()
    
    try:
        import json as json_lib
        
        # Get active employees (použij správný sloupec nebo odstraň filtr)
        employees = db.execute("SELECT id, name, skills, skill_score, training_hours_total, last_training_date FROM employees").fetchall()
        
        # Agregace skills
        all_skills = {}
        for emp in employees:
            try:
                skills = json_lib.loads(emp['skills']) if emp['skills'] and isinstance(emp['skills'], str) else (emp['skills'] or {})
            except:
                skills = {}
            
            if skills:
                for skill, level in skills.items():
                    if skill not in all_skills:
                        all_skills[skill] = {'total_level': 0, 'count': 0, 'employees': []}
                    all_skills[skill]['total_level'] += level
                    all_skills[skill]['count'] += 1
                    all_skills[skill]['employees'].append({
                        'id': emp['id'],
                        'name': emp['name'],
                        'level': level
                    })
        
        # Průměry
        for skill in all_skills:
            all_skills[skill]['avg_level'] = round(
                all_skills[skill]['total_level'] / all_skills[skill]['count'], 1
            )
        
        # Celkové skóre týmu
        team_skill_scores = [float(emp['skill_score'] or 50) for emp in employees]
        team_avg_score = sum(team_skill_scores) / len(team_skill_scores) if team_skill_scores else 50
        
        return jsonify({
            "ok": True,
            "team_score": round(team_avg_score, 1),
            "employees_count": len(employees),
            "skills": all_skills,
            "employees": [{
                "id": emp['id'],
                "name": emp['name'],
                "skill_score": float(emp['skill_score'] or 50),
                "skills": json_lib.loads(emp['skills']) if emp['skills'] and isinstance(emp['skills'], str) else (emp['skills'] or {}),
                "training_hours": float(emp['training_hours_total'] or 0),
                "last_training": emp['last_training_date'] if emp['last_training_date'] else None
            } for emp in employees]
        })
    except Exception as e:
        print(f"✗ Error getting team skills: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"ok": False, "error": "server_error", "message": str(e)}), 500


# Additional routes from main.py
@employees_bp.route('/api/team/stats', methods=['GET'])
@requires_role('owner', 'admin', 'manager', 'lander')
def api_team_stats():
    """API endpoint pro všechny team metriky"""
    u, err = require_auth()
    if err:
        return err
    
    db = get_db()
    try:
        from datetime import datetime, timedelta
        
        today = datetime.now()
        monday = today - timedelta(days=today.weekday())
        week_start = monday.strftime("%Y-%m-%d")
        week_end = (monday + timedelta(days=6)).strftime("%Y-%m-%d")
        
        stats = {
            'active_count': get_active_members_count(db),
            'average_utilization': get_average_utilization(db, week_start, week_end),
            'overloaded_count': get_overloaded_count(db, week_start, week_end),
            'ai_balance_score': get_ai_balance_score(db, week_start, week_end)
        }
        
        return jsonify({'ok': True, 'stats': stats})
    except Exception as e:
        print(f"[ERROR] api_team_stats: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'ok': False, 'error': str(e)}), 500

# ============================================================
# TEAM METRICS HELPER FUNCTIONS
# ============================================================

@employees_bp.route('/api/team/capacity-overview', methods=['GET'])
@requires_role('owner', 'admin', 'manager', 'lander')
def api_team_capacity_overview():
    """Přehled kapacit celého týmu"""
    u, err = require_auth()
    if err:
        return err
    
    db = get_db()
    try:
        from datetime import datetime, timedelta
        
        # Získej aktivní zaměstnance
        employees = db.execute("SELECT * FROM employees ORDER BY name").fetchall()
        
        today = datetime.now()
        monday = today - timedelta(days=today.weekday())
        week_start = monday.strftime("%Y-%m-%d")
        week_end = (monday + timedelta(days=6)).strftime("%Y-%m-%d")
        
        overview = {
            'total_capacity': 0,
            'used_capacity': 0,
            'overloaded_count': 0,
            'underutilized_count': 0,
            'members': []
        }
        
        for emp in employees:
            emp_dict = dict(emp)
            emp_id = emp_dict['id']
            
            # Získej profil
            profile = db.execute(
                "SELECT * FROM team_member_profile WHERE employee_id = ?",
                (emp_id,)
            ).fetchone()
            
            if not profile:
                # Vytvoř defaultní profil
                weekly_capacity = 40.0
            else:
                profile_dict = dict(profile)
                weekly_capacity = profile_dict.get('weekly_capacity_hours', 40.0)
            
            # Vypočítej aktuální hodiny tento týden
            timesheet_rows = db.execute(
                "SELECT SUM(COALESCE(duration_minutes, CAST(hours * 60 AS INTEGER))) / 60.0 as total FROM timesheets WHERE employee_id=? AND date >= ? AND date <= ?",
                (emp_id, week_start, week_end)
            ).fetchone()
            current_hours = round(timesheet_rows["total"] or 0, 1)
            
            capacity_percent = calculate_capacity_percent({'weekly_capacity_hours': weekly_capacity}, current_hours)
            capacity_status = calculate_capacity_status(capacity_percent)
            
            overview['total_capacity'] += weekly_capacity
            overview['used_capacity'] += current_hours
            
            if capacity_status == 'overloaded':
                overview['overloaded_count'] += 1
            elif capacity_status == 'underutilized':
                overview['underutilized_count'] += 1
            
            overview['members'].append({
                'id': emp_id,
                'name': emp_dict.get('name', ''),
                'capacity_percent': round(capacity_percent, 1),
                'status': capacity_status,
                'current_hours': current_hours,
                'weekly_capacity': weekly_capacity
            })
        
        overview['utilization_percent'] = round((overview['used_capacity'] / overview['total_capacity'] * 100) if overview['total_capacity'] > 0 else 0, 1)
        
        return jsonify({'ok': True, 'overview': overview})
    except Exception as e:
        print(f"[ERROR] api_team_capacity_overview: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'ok': False, 'error': str(e)}), 500

@employees_bp.route('/api/team/<int:employee_id>/skills', methods=['POST', 'PATCH'])
@requires_role('owner', 'admin', 'manager', 'lander')
def api_team_member_skills(employee_id):
    """Aktualizace dovedností člena týmu"""
    u, err = require_auth()
    if err:
        return err
    
    db = get_db()
    try:
        import json as json_lib
        
        # Zkontroluj, že zaměstnanec existuje
        employee = db.execute("SELECT id FROM employees WHERE id = ?", (employee_id,)).fetchone()
        if not employee:
            return jsonify({'ok': False, 'error': 'employee_not_found'}), 404
        
        data = request.get_json(force=True, silent=True) or {}
        
        # Získej nebo vytvoř profil
        profile = db.execute(
            "SELECT * FROM team_member_profile WHERE employee_id = ?",
            (employee_id,)
        ).fetchone()
        
        if not profile:
            # Vytvoř nový profil
            db.execute("""
                INSERT INTO team_member_profile (employee_id, weekly_capacity_hours)
                VALUES (?, 40.0)
            """, (employee_id,))
            db.commit()
            profile = db.execute(
                "SELECT * FROM team_member_profile WHERE employee_id = ?",
                (employee_id,)
            ).fetchone()
        
        # Aktualizuj data
        updates = []
        params = []
        
        if 'skills' in data:
            updates.append("skills = ?")
            params.append(json_lib.dumps(data['skills'] if isinstance(data['skills'], list) else []))
        
        if 'certifications' in data:
            updates.append("certifications = ?")
            params.append(json_lib.dumps(data['certifications'] if isinstance(data['certifications'], list) else []))
        
        if 'preferred_work_types' in data:
            updates.append("preferred_work_types = ?")
            params.append(json_lib.dumps(data['preferred_work_types'] if isinstance(data['preferred_work_types'], list) else []))
        
        if 'weekly_capacity_hours' in data:
            updates.append("weekly_capacity_hours = ?")
            params.append(float(data['weekly_capacity_hours']))
        
        if updates:
            updates.append("updated_at = datetime('now')")
            params.append(employee_id)
            
            db.execute(
                f"UPDATE team_member_profile SET {', '.join(updates)} WHERE employee_id = ?",
                params
            )
            db.commit()
        
        # Vrať aktualizovaný profil
        updated_profile = db.execute(
            "SELECT * FROM team_member_profile WHERE employee_id = ?",
            (employee_id,)
        ).fetchone()
        
        profile_dict = dict(updated_profile)
        try:
            profile_dict['skills'] = json_lib.loads(profile_dict.get('skills') or '[]')
            profile_dict['certifications'] = json_lib.loads(profile_dict.get('certifications') or '[]')
            profile_dict['preferred_work_types'] = json_lib.loads(profile_dict.get('preferred_work_types') or '[]')
        except:
            profile_dict['skills'] = []
            profile_dict['certifications'] = []
            profile_dict['preferred_work_types'] = []
        
        return jsonify({'ok': True, 'profile': profile_dict})
    except Exception as e:
        print(f"[ERROR] api_team_member_skills: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'ok': False, 'error': str(e)}), 500

@employees_bp.route('/api/team/member/<int:employee_id>', methods=['GET'])
@requires_role('owner', 'admin', 'manager', 'lander', 'worker')
def api_team_member_detail(employee_id):
    """Detail člena týmu s rozšířeným profilem"""
    u, err = require_auth()
    if err:
        return err
    
    db = get_db()
    try:
        import json as json_lib
        
        # Získej zaměstnance
        employee = db.execute("SELECT * FROM employees WHERE id = ?", (employee_id,)).fetchone()
        if not employee:
            return jsonify({'ok': False, 'error': 'employee_not_found'}), 404
        
        employee_dict = dict(employee)
        
        # Normalizace role
        employee_dict['role'] = normalize_employee_role(employee_dict.get('role'))
        
        # Účet zaměstnance
        if employee_dict.get('user_id'):
            user = db.execute("SELECT * FROM users WHERE id = ?", (employee_dict['user_id'],)).fetchone()
            if user:
                employee_dict['has_account'] = True
                employee_dict['account_role'] = normalize_role(dict(user).get('role'))
            else:
                employee_dict['has_account'] = False
        else:
            employee_dict['has_account'] = False
        
        # Vypočítej hodiny tento týden
        from datetime import datetime, timedelta
        today = datetime.now()
        monday = today - timedelta(days=today.weekday())
        week_start = monday.strftime("%Y-%m-%d")
        week_end = (monday + timedelta(days=6)).strftime("%Y-%m-%d")
        
        timesheet_rows = db.execute(
            "SELECT SUM(COALESCE(duration_minutes, CAST(hours * 60 AS INTEGER))) / 60.0 as total FROM timesheets WHERE employee_id=? AND date >= ? AND date <= ?",
            (employee_id, week_start, week_end)
        ).fetchone()
        employee_dict['hours_week'] = round(timesheet_rows["total"] or 0, 1)
        
        # Aktivní zakázky
        job_rows = db.execute(
            "SELECT COUNT(DISTINCT job_id) as count FROM job_assignments WHERE employee_id=?",
            (employee_id,)
        ).fetchone()
        employee_dict['active_projects'] = job_rows["count"] or 0
        
        # Získej nebo vytvoř profil
        profile = db.execute(
            "SELECT * FROM team_member_profile WHERE employee_id = ?",
            (employee_id,)
        ).fetchone()
        
        if not profile:
            # Vytvoř defaultní profil
            db.execute("""
                INSERT INTO team_member_profile (employee_id, weekly_capacity_hours)
                VALUES (?, 40.0)
            """, (employee_id,))
            db.commit()
            profile = db.execute(
                "SELECT * FROM team_member_profile WHERE employee_id = ?",
                (employee_id,)
            ).fetchone()
        
        profile_dict = dict(profile)
        
        # Parse JSON fields
        try:
            profile_dict['skills'] = json_lib.loads(profile_dict.get('skills') or '[]')
            profile_dict['certifications'] = json_lib.loads(profile_dict.get('certifications') or '[]')
            profile_dict['preferred_work_types'] = json_lib.loads(profile_dict.get('preferred_work_types') or '[]')
        except:
            profile_dict['skills'] = []
            profile_dict['certifications'] = []
            profile_dict['preferred_work_types'] = []
        
        # Vypočítej kapacitu
        current_week_hours = employee_dict.get('hours_week', 0)
        weekly_capacity = profile_dict.get('weekly_capacity_hours', 40.0)
        capacity_percent = calculate_capacity_percent(profile_dict, current_week_hours)
        capacity_status = calculate_capacity_status(capacity_percent)
        
        # Přidej vypočítané hodnoty do profilu
        profile_dict['capacity_percent'] = round(capacity_percent, 1)
        profile_dict['capacity_status'] = capacity_status
        profile_dict['current_week_hours'] = current_week_hours
        
        employee_dict['profile'] = profile_dict
        
        return jsonify({'ok': True, 'employee': employee_dict})
    except Exception as e:
        print(f"[ERROR] api_team_member_detail: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'ok': False, 'error': str(e)}), 500

@employees_bp.route('/api/team/init-profiles', methods=['POST'])
@requires_role('owner', 'admin')
def api_init_team_profiles():
    """Inicializační endpoint pro vytvoření profilů"""
    u, err = require_auth()
    if err:
        return err
    
    count = init_team_profiles()
    return jsonify({'ok': True, 'created': count, 'message': f'Vytvořeno {count} profilů'})


# ============================================================
# SMART PLANNER API
# ============================================================

