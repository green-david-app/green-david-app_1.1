# Green David App
from flask import Blueprint, jsonify, request, send_from_directory, render_template
from datetime import datetime, timedelta
from app.database import get_db
from app.utils.permissions import require_auth, require_role, requires_role
from app.utils.helpers import (
    audit_event, create_notification, _expand_assignees_with_delegate,
    _notify_assignees, _normalize_date
)
from assignment_helpers import (
    assign_employees_to_task, assign_employees_to_issue,
    get_task_assignees, get_issue_assignees,
    get_employee_tasks, get_employee_issues
)

tasks_bp = Blueprint('tasks', __name__)


@tasks_bp.route("/tasks.html")
def tasks_html():
    return send_from_directory(".", "tasks.html")


@tasks_bp.route("/issues.html")
def issues_html():
    return send_from_directory(".", "issues.html")


@tasks_bp.route("/issues")
def issues_page():
    return send_from_directory(".", "issues.html")


@tasks_bp.route("/recurring-tasks")
def recurring_tasks_page():
    return send_from_directory(".", "recurring-tasks.html")


# Tasks and Issues routes from main.py
@tasks_bp.route("/api/tasks", methods=["GET","POST","PATCH","PUT","DELETE"])
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
            priority = data.get("priority", "medium")
            if priority not in ["low", "medium", "high", "urgent"]:
                priority = "medium"
            
            db.execute("""
                INSERT INTO tasks(job_id, employee_id, title, description, status, due_date, priority, created_by, created_at, updated_at)
                VALUES (?,?,?,?,?,?,?,?,datetime('now'),datetime('now'))
            """, (
                int(data.get("job_id")) if data.get("job_id") else None,
                int(data.get("employee_id")) if data.get("employee_id") else None,
                title,
                (data.get("description") or "").strip(),
                (data.get("status") or "todo"),
                _normalize_date(data.get("due_date")) if data.get("due_date") else None,
                priority,
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
            allowed = ["title","description","status","due_date","employee_id","job_id","priority"]
            sets=[]; vals=[]
            for k in allowed:
                if k in data:
                    v = _normalize_date(data[k]) if k=="due_date" else data[k]
                    if k in ("employee_id","job_id") and v is not None:
                        v = int(v)
                    if k == "priority" and v not in ["low", "medium", "high", "urgent"]:
                        v = "medium"
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
        before = db.execute("SELECT id, job_id, employee_id, title, description, status, due_date, priority FROM tasks WHERE id=?", (tid,)).fetchone()
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
@tasks_bp.route("/api/issues", methods=["GET","POST","PATCH","DELETE"])
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
@tasks_bp.route("/api/tasks/<int:task_id>/attachments", methods=["GET", "POST", "DELETE"])
def api_task_attachments(task_id):
    u, err = require_role(write=(request.method != "GET"))
    if err: return err
    db = get_db()
    
    if request.method == "GET":
        rows = db.execute("""
            SELECT a.*, e.name as uploader_name
            FROM task_attachments a
            LEFT JOIN employees e ON e.id = a.uploaded_by
            WHERE a.task_id = ?
            ORDER BY a.uploaded_at DESC
        """, (task_id,)).fetchall()
        return jsonify({"ok": True, "attachments": [dict(r) for r in rows]})
    
    if request.method == "POST":
        if 'file' not in request.files:
            return jsonify({"ok": False, "error": "no_file"}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({"ok": False, "error": "empty_filename"}), 400
        
        if file and allowed_file(file.filename):
            original_filename = secure_filename(file.filename)
            ext = original_filename.rsplit('.', 1)[1].lower() if '.' in original_filename else ''
            filename = f"{uuid.uuid4().hex}.{ext}"
            filepath = os.path.join(UPLOAD_FOLDER, filename)
            
            file.save(filepath)
            file_size = os.path.getsize(filepath)
            
            db.execute("""
                INSERT INTO task_attachments (task_id, filename, original_filename, file_path, file_size, mime_type, uploaded_by)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (task_id, filename, original_filename, filepath, file_size, file.content_type, u["id"]))
            db.commit()
            
            return jsonify({"ok": True, "filename": original_filename})
        
        return jsonify({"ok": False, "error": "invalid_file_type"}), 400
    
    if request.method == "DELETE":
        att_id = request.args.get("id", type=int)
        if not att_id:
            return jsonify({"ok": False, "error": "missing_id"}), 400
        
        row = db.execute("SELECT file_path FROM task_attachments WHERE id = ?", (att_id,)).fetchone()
        if row and os.path.exists(row[0]):
            os.remove(row[0])
        
        db.execute("DELETE FROM task_attachments WHERE id = ?", (att_id,))
        db.commit()
        return jsonify({"ok": True})

@tasks_bp.route("/api/issues/<int:issue_id>/attachments", methods=["GET", "POST", "DELETE"])
def api_issue_attachments(issue_id):
    u, err = require_role(write=(request.method != "GET"))
    if err: return err
    db = get_db()
    
    if request.method == "GET":
        rows = db.execute("""
            SELECT a.*, e.name as uploader_name
            FROM issue_attachments a
            LEFT JOIN employees e ON e.id = a.uploaded_by
            WHERE a.issue_id = ?
            ORDER BY a.uploaded_at DESC
        """, (issue_id,)).fetchall()
        return jsonify({"ok": True, "attachments": [dict(r) for r in rows]})
    
    if request.method == "POST":
        if 'file' not in request.files:
            return jsonify({"ok": False, "error": "no_file"}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({"ok": False, "error": "empty_filename"}), 400
        
        if file and allowed_file(file.filename):
            original_filename = secure_filename(file.filename)
            ext = original_filename.rsplit('.', 1)[1].lower() if '.' in original_filename else ''
            filename = f"{uuid.uuid4().hex}.{ext}"
            filepath = os.path.join(UPLOAD_FOLDER, filename)
            
            file.save(filepath)
            file_size = os.path.getsize(filepath)
            
            db.execute("""
                INSERT INTO issue_attachments (issue_id, filename, original_filename, file_path, file_size, mime_type, uploaded_by)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (issue_id, filename, original_filename, filepath, file_size, file.content_type, u["id"]))
            db.commit()
            
            return jsonify({"ok": True, "filename": original_filename})
        
        return jsonify({"ok": False, "error": "invalid_file_type"}), 400
    
    if request.method == "DELETE":
        att_id = request.args.get("id", type=int)
        if not att_id:
            return jsonify({"ok": False, "error": "missing_id"}), 400
        
        row = db.execute("SELECT file_path FROM issue_attachments WHERE id = ?", (att_id,)).fetchone()
        if row and os.path.exists(row[0]):
            os.remove(row[0])
        
        db.execute("DELETE FROM issue_attachments WHERE id = ?", (att_id,))
        db.commit()
        return jsonify({"ok": True})

# Download attachment
@tasks_bp.route("/api/tasks/<int:task_id>/comments", methods=["GET", "POST"])
def api_task_comments(task_id):
    u, err = require_role(write=(request.method != "GET"))
    if err: return err
    db = get_db()
    
    if request.method == "GET":
        rows = db.execute("""
            SELECT c.*, e.name as author_name
            FROM task_comments c
            LEFT JOIN employees e ON e.id = c.user_id
            WHERE c.task_id = ?
            ORDER BY c.created_at ASC
        """, (task_id,)).fetchall()
        return jsonify({"ok": True, "comments": [dict(r) for r in rows]})
    
    data = request.get_json(force=True, silent=True) or {}
    comment = (data.get("comment") or "").strip()
    if not comment:
        return jsonify({"ok": False, "error": "empty_comment"}), 400
    
    db.execute("""
        INSERT INTO task_comments (task_id, user_id, comment)
        VALUES (?, ?, ?)
    """, (task_id, u["id"], comment))
    db.commit()
    return jsonify({"ok": True})

@tasks_bp.route("/api/issues/<int:issue_id>/comments", methods=["GET", "POST"])
def api_issue_comments(issue_id):
    u, err = require_role(write=(request.method != "GET"))
    if err: return err
    db = get_db()
    
    if request.method == "GET":
        rows = db.execute("""
            SELECT c.*, e.name as author_name
            FROM issue_comments c
            LEFT JOIN employees e ON e.id = c.user_id
            WHERE c.issue_id = ?
            ORDER BY c.created_at ASC
        """, (issue_id,)).fetchall()
        return jsonify({"ok": True, "comments": [dict(r) for r in rows]})
    
    data = request.get_json(force=True, silent=True) or {}
    comment = (data.get("comment") or "").strip()
    if not comment:
        return jsonify({"ok": False, "error": "empty_comment"}), 400
    
    db.execute("""
        INSERT INTO issue_comments (issue_id, user_id, comment)
        VALUES (?, ?, ?)
    """, (issue_id, u["id"], comment))
    db.commit()
    return jsonify({"ok": True})

# === LOCATIONS API ===
@tasks_bp.route("/api/tasks/<int:task_id>/location", methods=["GET", "POST", "DELETE"])
def api_task_location(task_id):
    u, err = require_role(write=(request.method != "GET"))
    if err: return err
    db = get_db()
    
    if request.method == "GET":
        row = db.execute("SELECT * FROM task_locations WHERE task_id = ? ORDER BY created_at DESC LIMIT 1", (task_id,)).fetchone()
        return jsonify({"ok": True, "location": dict(row) if row else None})
    
    if request.method == "POST":
        data = request.get_json(force=True, silent=True) or {}
        lat = data.get("latitude")
        lng = data.get("longitude")
        address = data.get("address", "")
        
        if lat is None or lng is None:
            return jsonify({"ok": False, "error": "missing_coordinates"}), 400
        
        # Delete old location
        db.execute("DELETE FROM task_locations WHERE task_id = ?", (task_id,))
        
        # Insert new
        db.execute("""
            INSERT INTO task_locations (task_id, latitude, longitude, address)
            VALUES (?, ?, ?, ?)
        """, (task_id, float(lat), float(lng), address))
        db.commit()
        return jsonify({"ok": True})
    
    if request.method == "DELETE":
        db.execute("DELETE FROM task_locations WHERE task_id = ?", (task_id,))
        db.commit()
        return jsonify({"ok": True})

@tasks_bp.route("/api/issues/<int:issue_id>/location", methods=["GET", "POST", "DELETE"])
def api_issue_location(issue_id):
    u, err = require_role(write=(request.method != "GET"))
    if err: return err
    db = get_db()
    
    if request.method == "GET":
        row = db.execute("SELECT * FROM issue_locations WHERE issue_id = ? ORDER BY created_at DESC LIMIT 1", (issue_id,)).fetchone()
        return jsonify({"ok": True, "location": dict(row) if row else None})
    
    if request.method == "POST":
        data = request.get_json(force=True, silent=True) or {}
        lat = data.get("latitude")
        lng = data.get("longitude")
        address = data.get("address", "")
        
        if lat is None or lng is None:
            return jsonify({"ok": False, "error": "missing_coordinates"}), 400
        
        # Delete old location
        db.execute("DELETE FROM issue_locations WHERE issue_id = ?", (issue_id,))
        
        # Insert new
        db.execute("""
            INSERT INTO issue_locations (issue_id, latitude, longitude, address)
            VALUES (?, ?, ?, ?)
        """, (issue_id, float(lat), float(lng), address))
        db.commit()
        return jsonify({"ok": True})
    
    if request.method == "DELETE":
        db.execute("DELETE FROM issue_locations WHERE issue_id = ?", (issue_id,))
        db.commit()
        return jsonify({"ok": True})

@tasks_bp.route("/gd/api/tasks", methods=["GET", "POST", "PATCH", "PUT", "DELETE"])
def gd_api_tasks():
    return api_tasks()

@tasks_bp.route("/gd/api/employees", methods=["GET", "POST", "PATCH", "DELETE"])
def gd_api_employees():
    return api_employees()

@tasks_bp.route("/gd/api/timesheets", methods=["GET", "POST", "PATCH", "DELETE"])
def gd_api_timesheets():
    return api_timesheets()

# Helper function to get hourly rate (hierarchy: job override > employee rate > global default)

# Additional routes from main.py
@tasks_bp.route("/api/filters/tasks", methods=["GET"])
def api_task_filters():
    """Chytré filtry pro úkoly"""
    u, err = require_role()
    if err: return err
    
    filter_type = request.args.get("filter", "all")
    db = get_db()
    
    # Base query
    base_query = """
        SELECT t.*, j.name as job_name
        FROM tasks t
        LEFT JOIN jobs j ON j.id = t.job_id
    """
    
    # Apply filters
    if filter_type == "my_today":
        # Moje úkoly s deadlinem dnes
        rows = db.execute(base_query + """
            INNER JOIN task_assignments ta ON ta.task_id = t.id
            WHERE ta.employee_id = ?
            AND DATE(t.deadline) = DATE('now')
            AND t.status != 'completed'
            ORDER BY t.deadline ASC, t.id DESC
        """, (u["id"],)).fetchall()
    
    elif filter_type == "my_overdue":
        # Moje přetažené úkoly
        rows = db.execute(base_query + """
            INNER JOIN task_assignments ta ON ta.task_id = t.id
            WHERE ta.employee_id = ?
            AND DATE(t.deadline) < DATE('now')
            AND t.status != 'completed'
            ORDER BY t.deadline ASC
        """, (u["id"],)).fetchall()
    
    elif filter_type == "my_week":
        # Moje úkoly tento týden
        rows = db.execute(base_query + """
            INNER JOIN task_assignments ta ON ta.task_id = t.id
            WHERE ta.employee_id = ?
            AND DATE(t.deadline) BETWEEN DATE('now') AND DATE('now', '+7 days')
            AND t.status != 'completed'
            ORDER BY t.deadline ASC
        """, (u["id"],)).fetchall()
    
    elif filter_type == "high_priority":
        # Vysoká priorita
        rows = db.execute(base_query + """
            WHERE t.status != 'completed'
            ORDER BY t.deadline ASC
        """).fetchall()
    
    elif filter_type == "unassigned":
        # Nepřiřazené úkoly
        rows = db.execute(base_query + """
            LEFT JOIN task_assignments ta ON ta.task_id = t.id
            WHERE ta.id IS NULL
            AND t.status != 'completed'
            ORDER BY t.created_at DESC
        """).fetchall()
    
    else:
        # All tasks
        rows = db.execute(base_query + """
            WHERE t.status != 'completed'
            ORDER BY t.created_at DESC
            LIMIT 50
        """).fetchall()
    
    tasks = []
    for task in rows:
        task_dict = dict(task)
        # Zajisti, že priority je ve výstupu (default 'medium' pokud není nastaveno)
        if "priority" not in task_dict or task_dict["priority"] is None:
            task_dict["priority"] = "medium"
        task_dict["assignees"] = get_task_assignees(db, task["id"])
        tasks.append(task_dict)
    
    return jsonify({"ok": True, "tasks": tasks, "filter": filter_type})


@tasks_bp.route("/api/filters/issues", methods=["GET"])
def api_issue_filters():
    """Chytré filtry pro issues"""
    u, err = require_role()
    if err: return err
    
    filter_type = request.args.get("filter", "all")
    db = get_db()
    
    base_query = """
        SELECT i.*, j.name as job_name
        FROM issues i
        LEFT JOIN jobs j ON j.id = i.job_id
    """
    
    if filter_type == "blockers":
        # Blokující issues
        rows = db.execute(base_query + """
            WHERE i.type = 'blocker'
            AND i.status = 'open'
            ORDER BY i.created_at DESC
        """).fetchall()
    
    elif filter_type == "my_issues":
        # Moje issues
        rows = db.execute(base_query + """
            INNER JOIN issue_assignments ia ON ia.issue_id = i.id
            WHERE ia.employee_id = ?
            AND i.status = 'open'
            ORDER BY i.created_at DESC
        """, (u["id"],)).fetchall()
    
    elif filter_type == "critical":
        # Kritické severity
        rows = db.execute(base_query + """
            WHERE i.severity = 'critical'
            AND i.status = 'open'
            ORDER BY i.created_at DESC
        """).fetchall()
    
    elif filter_type == "recent":
        # Nedávno vytvořené (48h)
        rows = db.execute(base_query + """
            WHERE datetime(i.created_at) >= datetime('now', '-2 days')
            ORDER BY i.created_at DESC
        """).fetchall()
    
    else:
        # All open issues
        rows = db.execute(base_query + """
            WHERE i.status = 'open'
            ORDER BY i.created_at DESC
            LIMIT 50
        """).fetchall()
    
    issues = []
    for issue in rows:
        issue_dict = dict(issue)
        issue_dict["assignees"] = get_issue_assignees(db, issue["id"])
        issues.append(issue_dict)
    
    return jsonify({"ok": True, "issues": issues, "filter": filter_type})


# ----------------- BULK OPERATIONS -----------------
@tasks_bp.route("/api/bulk/tasks", methods=["POST"])
def api_bulk_tasks():
    """Hromadné operace na úkolech"""
    u, err = require_role(write=True)
    if err: return err
    
    data = request.get_json(force=True, silent=True) or {}
    task_ids = data.get("task_ids", [])
    action = data.get("action", "")
    
    if not task_ids or not action:
        return jsonify({"ok": False, "error": "missing_params"}), 400
    
    db = get_db()
    affected = 0
    
    try:
        if action == "complete":
            # Označit jako dokončené
            placeholders = ','.join('?' * len(task_ids))
            db.execute(f"""
                UPDATE tasks 
                SET status = 'completed', completed_at = datetime('now')
                WHERE id IN ({placeholders})
            """, task_ids)
            affected = db.total_changes
        
        elif action == "delete":
            # Smazat úkoly
            placeholders = ','.join('?' * len(task_ids))
            db.execute(f"DELETE FROM tasks WHERE id IN ({placeholders})", task_ids)
            affected = db.total_changes
        
        elif action == "assign":
            # Přiřadit zaměstnance
            employee_ids = data.get("employee_ids", [])
            if not employee_ids:
                return jsonify({"ok": False, "error": "missing_employees"}), 400
            
            for task_id in task_ids:
                # Remove old assignments
                db.execute("DELETE FROM task_assignments WHERE task_id = ?", (task_id,))
                # Add new assignments
                for idx, emp_id in enumerate(employee_ids):
                    db.execute("""
                        INSERT INTO task_assignments (task_id, employee_id, is_primary)
                        VALUES (?, ?, ?)
                    """, (task_id, emp_id, 1 if idx == 0 else 0))
            affected = len(task_ids)
        
        elif action == "change_status":
            # Změnit stav
            new_status = data.get("status", "")
            if new_status not in ["pending", "in_progress", "completed", "blocked"]:
                return jsonify({"ok": False, "error": "invalid_status"}), 400
            
            placeholders = ','.join('?' * len(task_ids))
            db.execute(f"""
                UPDATE tasks 
                SET status = ?
                WHERE id IN ({placeholders})
            """, [new_status] + task_ids)
            affected = db.total_changes
        
        elif action == "change_priority":
            # Změnit prioritu
            new_priority = data.get("priority", "")
            if new_priority not in ["low", "medium", "high", "urgent"]:
                return jsonify({"ok": False, "error": "invalid_priority"}), 400
            
            placeholders = ','.join('?' * len(task_ids))
            db.execute(f"""
                UPDATE tasks 
                SET priority = ?
                WHERE id IN ({placeholders})
            """, [new_priority] + task_ids)
            affected = db.total_changes
        
        else:
            return jsonify({"ok": False, "error": "unknown_action"}), 400
        
        db.commit()
        return jsonify({"ok": True, "affected": affected})
    
    except Exception as e:
        db.rollback()
        return jsonify({"ok": False, "error": str(e)}), 500


@tasks_bp.route("/api/bulk/issues", methods=["POST"])
def api_bulk_issues():
    """Hromadné operace na issues"""
    u, err = require_role(write=True)
    if err: return err
    
    data = request.get_json(force=True, silent=True) or {}
    issue_ids = data.get("issue_ids", [])
    action = data.get("action", "")
    
    if not issue_ids or not action:
        return jsonify({"ok": False, "error": "missing_params"}), 400
    
    db = get_db()
    affected = 0
    
    try:
        if action == "resolve":
            # Vyřešit issues
            placeholders = ','.join('?' * len(issue_ids))
            db.execute(f"""
                UPDATE issues 
                SET status = 'resolved', resolved_at = datetime('now')
                WHERE id IN ({placeholders})
            """, issue_ids)
            affected = db.total_changes
        
        elif action == "delete":
            # Smazat issues
            placeholders = ','.join('?' * len(issue_ids))
            db.execute(f"DELETE FROM issues WHERE id IN ({placeholders})", issue_ids)
            affected = db.total_changes
        
        elif action == "assign":
            # Přiřadit zaměstnance
            employee_ids = data.get("employee_ids", [])
            if not employee_ids:
                return jsonify({"ok": False, "error": "missing_employees"}), 400
            
            for issue_id in issue_ids:
                db.execute("DELETE FROM issue_assignments WHERE issue_id = ?", (issue_id,))
                for idx, emp_id in enumerate(employee_ids):
                    db.execute("""
                        INSERT INTO issue_assignments (issue_id, employee_id, is_primary)
                        VALUES (?, ?, ?)
                    """, (issue_id, emp_id, 1 if idx == 0 else 0))
            affected = len(issue_ids)
        
        elif action == "change_severity":
            # Změnit závažnost
            new_severity = data.get("severity", "")
            if new_severity not in ["low", "medium", "high", "critical"]:
                return jsonify({"ok": False, "error": "invalid_severity"}), 400
            
            placeholders = ','.join('?' * len(issue_ids))
            db.execute(f"""
                UPDATE issues 
                SET severity = ?
                WHERE id IN ({placeholders})
            """, [new_severity] + issue_ids)
            affected = db.total_changes
        
        else:
            return jsonify({"ok": False, "error": "unknown_action"}), 400
        
        db.commit()
        return jsonify({"ok": True, "affected": affected})
    
    except Exception as e:
        db.rollback()
        return jsonify({"ok": False, "error": str(e)}), 500


# ============================================================================
# JOBS EXTENDED API - Rozšířené zakázky
# ============================================================================

