
from flask import Flask, render_template, jsonify, request, g
import sqlite3
import os

DB_PATH = os.environ.get("GD_DB_PATH", "app.db")

app = Flask(__name__)

# ----------------------- DB helpers -----------------------
def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(DB_PATH)
        g.db.row_factory = sqlite3.Row
    return g.db

@app.teardown_appcontext
def close_db(exc):
    db = g.pop("db", None)
    if db is not None:
        db.close()

def ensure_tables():
    db = get_db()
    db.execute("""
        CREATE TABLE IF NOT EXISTS employees (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            role TEXT NOT NULL
        )
    """)
    db.commit()

# ----------------------- Template routes -----------------------
@app.route("/")
def index():
    return render_template("calendar.html")

@app.route("/calendar")
def calendar_page():
    return render_template("calendar.html")

@app.route("/timesheets")
def timesheets_page():
    return render_template("timesheets.html")

@app.route("/employees")
def employees_page():
    return render_template("employees.html")

@app.route("/jobs")
def jobs_page():
    return render_template("jobs.html")

@app.route("/tasks")
def tasks_page():
    return render_template("tasks.html")

@app.route("/warehouse")
def warehouse_page():
    return render_template("warehouse.html")

@app.route("/users")
def users_page():
    return render_template("users.html")

# ----------------------- Employees API -----------------------
@app.route("/api/employees", methods=["GET", "POST"])
def api_employees():
    ensure_tables()
    db = get_db()

    if request.method == "GET":
        role = request.args.get("role")
        if role:
            rows = db.execute(
                "SELECT id, name, role FROM employees WHERE role=? ORDER BY id DESC",
                (role,),
            ).fetchall()
        else:
            rows = db.execute(
                "SELECT id, name, role FROM employees ORDER BY id DESC"
            ).fetchall()
        return jsonify({"ok": True, "employees": [dict(r) for r in rows]})

    # POST (create)
    data = request.get_json(force=True) or {}
    name = (data.get("name") or "").strip()
    role = (data.get("role") or "zahradník").strip()
    if not name:
        return jsonify({"ok": False, "error": "Jméno je povinné"}), 400

    cur = db.execute("INSERT INTO employees (name, role) VALUES (?, ?)", (name, role))
    db.commit()
    return jsonify({"ok": True, "id": cur.lastrowid}), 201

@app.route("/api/employees/<int:emp_id>", methods=["GET", "PUT", "DELETE"])
def api_employee_detail(emp_id):
    ensure_tables()
    db = get_db()

    if request.method == "GET":
        row = db.execute("SELECT id, name, role FROM employees WHERE id=?", (emp_id,)).fetchone()
        if not row:
            return jsonify({"ok": False, "error": "Nenalezeno"}), 404
        return jsonify({"ok": True, "employee": dict(row)})

    if request.method == "PUT":
        data = request.get_json(force=True) or {}
        fields = []
        params = []
        if "name" in data:
            fields.append("name=?")
            params.append((data.get("name") or "").strip())
        if "role" in data:
            fields.append("role=?")
            params.append((data.get("role") or "").strip())
        if not fields:
            return jsonify({"ok": False, "error": "Nic k aktualizaci"}), 400
        params.append(emp_id)
        db.execute(f"UPDATE employees SET {', '.join(fields)} WHERE id=?", tuple(params))
        db.commit()
        return jsonify({"ok": True})

    # DELETE
    db.execute("DELETE FROM employees WHERE id=?", (emp_id,))
    db.commit()
    return jsonify({"ok": True})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8000)))
