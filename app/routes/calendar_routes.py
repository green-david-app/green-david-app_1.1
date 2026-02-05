# Green David App
from flask import Blueprint, jsonify, request, send_from_directory, render_template
from datetime import datetime, timedelta
from app.database import get_db
from app.utils.permissions import require_auth, require_role

calendar_bp = Blueprint('calendar', __name__)


@calendar_bp.route("/calendar.html")
def calendar_html():
    return render_template("calendar.html", page_title="Kalendář")


# Calendar routes from main.py
@calendar_bp.route("/api/calendar", methods=["GET", "POST", "PATCH"])
def api_calendar():
    db = get_db()
    if request.method == "GET":
        month_str = request.args.get("month")
        date_str = request.args.get("date")
        from_str = request.args.get("from")
        to_str = request.args.get("to")
        
        q = "SELECT id, date, title, kind, job_id, start_time, end_time, note, color FROM calendar_events WHERE 1=1"
        params = []
        
        if month_str:
            try:
                year, month = [int(x) for x in month_str.split("-")]
                q += " AND strftime('%Y-%m', date) = ?"
                params.append(month_str)
            except Exception:
                pass
        elif date_str:
            q += " AND date = ?"
            params.append(_normalize_date(date_str))
        elif from_str or to_str:
            if from_str:
                q += " AND date >= ?"
                params.append(_normalize_date(from_str))
            if to_str:
                q += " AND date <= ?"
                params.append(_normalize_date(to_str))
        
        q += " ORDER BY date ASC, id ASC"
        rows = [dict(r) for r in db.execute(q, params).fetchall()]
        return jsonify({"ok": True, "events": rows, "items": rows})
    
    u, err = require_auth()
    if err: return err
    
    data = request.get_json(force=True, silent=True) or {}
    
    if request.method == "POST":
        try:
            title = (data.get("title") or "").strip()
            date_str = _normalize_date(data.get("date"))
            kind = (data.get("kind") or data.get("type") or "note").strip()
            color = (data.get("color") or "#2e7d32").strip()
            note = (data.get("note") or data.get("details") or "").strip()
            job_id = data.get("job_id")
            start_time = data.get("start_time") or ""
            end_time = data.get("end_time") or ""
            
            if not title or not date_str:
                return jsonify({"ok": False, "error": "missing_fields"}), 400
            
            db.execute(
                "INSERT INTO calendar_events(date, title, kind, job_id, start_time, end_time, note, color) VALUES (?,?,?,?,?,?,?,?)",
                (date_str, title, kind, job_id, start_time, end_time, note, color)
            )
            db.commit()
            print(f"✓ Calendar event '{title}' created successfully")
            return jsonify({"ok": True})
        except Exception as e:
            db.rollback()
            print(f"✗ Error creating calendar event: {e}")
            return jsonify({"ok": False, "error": str(e)}), 500
    
    # PATCH
    try:
        ev_id = data.get("id")
        if not ev_id:
            return jsonify({"ok": False, "error": "missing_id"}), 400
        
        updates = []
        params = []
        allowed = ["title", "date", "kind", "type", "color", "note", "details", "job_id", "start_time", "end_time"]
        for k in allowed:
            if k in data:
                if k == "date":
                    params.append(_normalize_date(data[k]))
                elif k == "type":
                    params.append(data[k])
                    updates.append("kind=?")
                    continue
                elif k == "details":
                    params.append(data[k])
                    updates.append("note=?")
                    continue
                else:
                    params.append(data[k])
                updates.append(f"{k}=?")
        
        if not updates:
            return jsonify({"ok": False, "error": "nothing_to_update"}), 400
        
        params.append(int(ev_id))
        db.execute("UPDATE calendar_events SET " + ", ".join(updates) + " WHERE id=?", params)
        db.commit()
        print(f"✓ Calendar event {ev_id} updated successfully")
        return jsonify({"ok": True})
    except Exception as e:
        db.rollback()
        print(f"✗ Error updating calendar event: {e}")
        return jsonify({"ok": False, "error": str(e)}), 500

@calendar_bp.route("/api/calendar/<int:event_id>", methods=["DELETE"])
def api_calendar_delete(event_id):
    u, err = require_auth()
    if err: return err
    db = get_db()
    try:
        db.execute("DELETE FROM calendar_events WHERE id=?", (event_id,))
        db.commit()
        print(f"✓ Calendar event {event_id} deleted successfully")
        return jsonify({"ok": True})
    except Exception as e:
        db.rollback()
        print(f"✗ Error deleting calendar event: {e}")
        return jsonify({"ok": False, "error": str(e)}), 500

# ----------------- /gd/api/ aliases -----------------
@calendar_bp.route("/gd/api/calendar", methods=["GET", "POST", "PATCH"])
def gd_api_calendar():
    return api_calendar()

@calendar_bp.route("/gd/api/calendar/<int:event_id>", methods=["DELETE"])
def gd_api_calendar_delete(event_id):
    return api_calendar_delete(event_id)


# Přidej tyto endpointy do main.py

# ----------------- GLOBAL SEARCH -----------------
@calendar_bp.route("/api/search", methods=["GET"])
def api_global_search():
    """Globální vyhledávání napříč zakázkami, úkoly, issues a zaměstnanci"""
    u, err = require_role()
    if err: return err
    
    query = request.args.get("q", "").strip()
    if not query or len(query) < 2:
        return jsonify({"ok": True, "results": {"jobs": [], "tasks": [], "issues": [], "employees": []}})
    
    db = get_db()
    search_term = f"%{query}%"
    
    # Choose best available timestamp for ordering jobs (schema differs across versions)
    if _table_has_column(db, "jobs", "created_at"):
        jobs_order = "datetime(created_at) DESC, id DESC"
    elif _table_has_column(db, "jobs", "created_date"):
        jobs_order = "datetime(created_date) DESC, id DESC"
    elif _table_has_column(db, "jobs", "date"):
        jobs_order = "date(date) DESC, id DESC"
    else:
        jobs_order = "id DESC"

    # Search Jobs
    # NOTE: Schéma "jobs" se v různých verzích liší. V této aplikaci má tabulka jobs
    # typicky sloupce: name/title, client, city, note, code, created_at. Původní varianta
    # používala description/customer/address, které v DB nejsou.
    jobs = db.execute(f"""
        SELECT
            id,
            COALESCE(title, name, '') AS name,
            note AS description,
            client AS customer,
            city AS address,
            status
        FROM jobs
        WHERE COALESCE(title, name, '') LIKE ?
           OR client LIKE ?
           OR city LIKE ?
           OR note LIKE ?
           OR code LIKE ?
        ORDER BY {jobs_order}
        LIMIT 10
    """, (search_term, search_term, search_term, search_term, search_term)).fetchall()
    
    # Search Tasks (including assigned employees)
    tasks = db.execute("""
        SELECT DISTINCT t.id, t.job_id, t.title, t.description, t.status, t.due_date,
               COALESCE(j.title, j.name, '') as job_name
        FROM tasks t
        LEFT JOIN jobs j ON j.id = t.job_id
        LEFT JOIN task_assignments ta ON ta.task_id = t.id
        LEFT JOIN employees e ON e.id = ta.employee_id
        WHERE t.title LIKE ? 
           OR t.description LIKE ?
           OR e.name LIKE ?
        ORDER BY t.created_at DESC
        LIMIT 10
    """, (search_term, search_term, search_term)).fetchall()
    
    # Search Issues (including assigned employees)
    issues = db.execute("""
        SELECT DISTINCT i.id, i.job_id, i.title, i.description, i.type, i.status, i.severity,
               COALESCE(j.title, j.name, '') as job_name
        FROM issues i
        LEFT JOIN jobs j ON j.id = i.job_id
        LEFT JOIN issue_assignments ia ON ia.issue_id = i.id
        LEFT JOIN employees e ON e.id = ia.employee_id
        WHERE i.title LIKE ? 
           OR i.description LIKE ?
           OR e.name LIKE ?
        ORDER BY i.created_at DESC
        LIMIT 10
    """, (search_term, search_term, search_term)).fetchall()
    
    # Search Employees
    employees = db.execute("""
        SELECT id, name, email, phone, role
        FROM employees
        WHERE name LIKE ? OR email LIKE ? OR phone LIKE ?
        ORDER BY name
        LIMIT 10
    """, (search_term, search_term, search_term)).fetchall()
    
    return jsonify({
        "ok": True,
        "query": query,
        "results": {
            "jobs": [dict(r) for r in jobs],
            "tasks": [dict(r) for r in tasks],
            "issues": [dict(r) for r in issues],
            "employees": [dict(r) for r in employees]
        },
        "total": len(jobs) + len(tasks) + len(issues) + len(employees)
    })


# ----------------- SMART FILTERS -----------------
