# ---- BEGIN PATCH 2025-11-09 (api_tasks) ----
from datetime import datetime, timezone
from flask import Blueprint, request, jsonify

# If you already have this route in main.py, replace just the POST/PATCH/DELETE blocks
# with the bodies below.

@app.route("/api/tasks", methods=["GET","POST","PATCH","DELETE"])
def api_tasks():
    db = get_db()
    if request.method == "GET":
        rows = db.execute("SELECT id, job_id, employee_id, title, description, status, due_date, created_at FROM tasks ORDER BY created_at DESC").fetchall()
        return jsonify({"rows":[dict(r) for r in rows]})

    if request.method == "POST":
        data = request.get_json(silent=True) or request.form
        now_iso = datetime.now(timezone.utc).isoformat(timespec="seconds")
        db.execute(
            "INSERT INTO tasks(job_id, employee_id, title, description, status, due_date, created_at) VALUES (?,?,?,?,?,?,?)",
            (
                data.get("job_id"),
                data.get("employee_id"),
                (data.get("title") or "").strip() or "bez názvu",
                data.get("description"),
                (data.get("status") or "open"),
                (data.get("due_date")),
                data.get("created_at") or now_iso,
            ),
        )
        db.commit()
        new_id = db.execute("SELECT last_insert_rowid() AS id").fetchone()["id"]
        row = db.execute("SELECT * FROM tasks WHERE id=?", (new_id,)).fetchone()
        return jsonify({"ok": True, "id": new_id, "row": dict(row)}), 201

    if request.method == "PATCH":
        data = request.get_json(force=True)
        if not data or "id" not in data:
            return jsonify({"error":"missing id"}), 400
        fields, params = [], []
        for col in ("job_id","employee_id","title","description","status","due_date"):
            if col in data:
                fields.append(f"{col}=?")
                params.append(data[col])
        if not fields:
            return jsonify({"ok": True})
        params.append(data["id"])
        db.execute(f"UPDATE tasks SET {', '.join(fields)} WHERE id=?", params)
        db.commit()
        row = db.execute("SELECT * FROM tasks WHERE id=?", (data["id"],)).fetchone()
        return jsonify({"ok": True, "row": dict(row)})

    if request.method == "DELETE":
        task_id = request.args.get("id")
        if not task_id:
            return jsonify({"error":"missing id"}), 400
        db.execute("DELETE FROM tasks WHERE id=?", (task_id,))
        db.commit()
        return jsonify({"ok": True})
# ---- END PATCH 2025-11-09 ----