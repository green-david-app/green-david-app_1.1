import os, sqlite3
from flask import Flask, jsonify, request, g, render_template, send_from_directory

DB_PATH = os.environ.get("DB_PATH", "app.db")
SECRET_KEY = os.environ.get("SECRET_KEY", "dev-" + os.urandom(16).hex())

app = Flask(__name__, static_folder=".", static_url_path="")
app.secret_key = SECRET_KEY

def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(DB_PATH)
        g.db.row_factory = sqlite3.Row
    return g.db

@app.teardown_appcontext
def close_db(error=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()

def ensure_schema():
    db = get_db()
    db.execute("CREATE TABLE IF NOT EXISTS users(id INTEGER PRIMARY KEY AUTOINCREMENT, email TEXT UNIQUE, name TEXT, role TEXT DEFAULT 'admin', password_hash TEXT, active INTEGER DEFAULT 1)")
    db.execute("CREATE TABLE IF NOT EXISTS employees(id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL, role TEXT NOT NULL DEFAULT 'zahradník')")
    db.commit()

@app.before_request
def _ensure():
    ensure_schema()

# ---------- base ----------
@app.route("/")
def index():
    return send_from_directory(".", "index.html")

# ---------- simple /api/me so frontend doesn't crash ----------
@app.route("/api/me")
def api_me():
    return jsonify({"ok": True, "authenticated": True, "user": {"id":1,"email":"admin@greendavid.local","name":"Admin","role":"admin","active":1}, "tasks_count": 0})

# ---------- employees API ----------
@app.route("/api/employees", methods=["GET", "POST", "PATCH", "DELETE"])
def api_employees():
    db = get_db()
    if request.method == "GET":
        rows = [dict(r) for r in db.execute("SELECT * FROM employees ORDER BY id DESC")]
        return jsonify({"ok": True, "employees": rows})
    if request.method == "POST":
        data = request.get_json(force=True, silent=True) or {}
        name = (data.get("name") or "").strip()
        role = (data.get("role") or "zahradník").strip() or "zahradník"
        if not name:
            return jsonify({"ok": False, "error":"invalid_input"}), 400
        db.execute("INSERT INTO employees(name,role) VALUES (?,?)", (name, role))
        db.commit()
        return jsonify({"ok": True})
    if request.method == "PATCH":
        data = request.get_json(force=True, silent=True) or {}
        eid = data.get("id")
        if not eid: return jsonify({"ok": False, "error":"missing_id"}), 400
        sets=[]; vals=[]
        if "name" in data: sets.append("name=?"); vals.append(data["name"])
        if "role" in data: sets.append("role=?"); vals.append(data["role"] or "zahradník")
        if not sets: return jsonify({"ok": False, "error":"no_fields"}), 400
        vals.append(int(eid))
        db.execute("UPDATE employees SET "+",".join(sets)+" WHERE id=?", vals)
        db.commit()
        return jsonify({"ok": True})
    # DELETE
    eid = request.args.get("id", type=int)
    if not eid: return jsonify({"ok": False, "error":"missing_id"}), 400
    db.execute("DELETE FROM employees WHERE id=?", (eid,))
    db.commit()
    return jsonify({"ok": True})

# ---------- pages ----------
@app.route("/employees")
def page_employees():
    return render_template("employees.html")

@app.route("/brigadnici.html")
def page_brigadnici():
    return render_template("brigadnici.html")
