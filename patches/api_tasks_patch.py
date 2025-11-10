from flask import request, jsonify, abort
import sqlite3

def _normalize_date(value):
    # Accepts "YYYY-MM-DD" or ISO; returns "YYYY-MM-DD" for storage
    if not value:
        return None
    v = str(value).strip()
    # keep first 10 chars (YYYY-MM-DD)
    return v[:10]

@app.route("/api/tasks", methods=["GET", "POST", "PATCH", "PUT", "DELETE"])
def api_tasks():
    db = get_db()  # assumes you have a helper returning sqlite3.Connection with row_factory
    m = request.method

    if m == "GET":
        task_id = request.args.get("id")
        if task_id:
            row = db.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()
            if not row:
                return jsonify({"error": "not_found"}), 404
            return jsonify(dict(row))
        else:
            rows = db.execute("SELECT * FROM tasks ORDER BY created_at DESC").fetchall()
            return jsonify([dict(r) for r in rows])

    if m == "POST":
        data = request.get_json(silent=True) or request.form
        try:
            db.execute(
                """
                INSERT INTO tasks (job_id, employee_id, title, description, status, due_date, created_at)
                VALUES (?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                """,
                (
                    data.get("job_id"),
                    data.get("employee_id"),
                    (data.get("title") or "").strip(),
                    (data.get("description") or "").strip(),
                    (data.get("status") or "open").strip(),
                    _normalize_date(data.get("due_date")) if data.get("due_date") else None,
                ),
            )
            db.commit()
            new_id = db.execute("SELECT last_insert_rowid() AS id").fetchone()["id"]
            row = db.execute("SELECT * FROM tasks WHERE id = ?", (new_id,)).fetchone()
            return jsonify(dict(row)), 201
        except sqlite3.IntegrityError as e:
            db.rollback()
            return jsonify({"error": "integrity_error", "detail": str(e)}), 400

    if m in ("PATCH", "PUT"):
        data = request.get_json(silent=True) or request.form
        task_id = data.get("id") or request.args.get("id")
        if not task_id:
            return jsonify({"error": "missing_id"}), 400

        # Build dynamic update
        fields, params = [], []
        for k in ("job_id", "employee_id", "title", "description", "status", "due_date"):
            if k in data and data.get(k) is not None:
                v = data.get(k)
                if k == "due_date":
                    v = _normalize_date(v)
                fields.append(f"{k} = ?")
                params.append(v)

        if not fields:
            return jsonify({"error": "nothing_to_update"}), 400

        params.append(task_id)
        db.execute(f"UPDATE tasks SET {', '.join(fields)} WHERE id = ?", params)
        db.commit()
        row = db.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()
        return jsonify(dict(row)), 200

    if m == "DELETE":
        task_id = request.args.get("id") or (request.get_json(silent=True) or {}).get("id")
        if not task_id:
            return jsonify({"error": "missing_id"}), 400
        db.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
        db.commit()
        return jsonify({"ok": True, "deleted": int(task_id)}), 200

    abort(405)
