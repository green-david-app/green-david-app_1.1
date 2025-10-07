
import os, sqlite3, secrets, io
from datetime import datetime, date
from flask import Flask, request, session, g, redirect, render_template, jsonify, flash, Response, send_file
from werkzeug.security import generate_password_hash, check_password_hash

DB_PATH = os.environ.get("DB_PATH", "app.db")
SECRET_KEY = os.environ.get("SECRET_KEY", "dev-" + os.urandom(16).hex())

app = Flask(__name__, static_folder="static", static_url_path="/static", template_folder="templates")
app.secret_key = SECRET_KEY

def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(DB_PATH)
        g.db.row_factory = sqlite3.Row
    return g.db

@app.teardown_appcontext
def close_db(exc=None):
    db = g.pop("db", None)
    if db: db.close()

def init_db():
    db = get_db()
    db.executescript("""
    PRAGMA foreign_keys = ON;
    CREATE TABLE IF NOT EXISTS users(
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      email TEXT UNIQUE NOT NULL,
      name TEXT,
      role TEXT NOT NULL DEFAULT 'user',
      password_hash TEXT NOT NULL,
      approved INTEGER NOT NULL DEFAULT 0,
      active INTEGER NOT NULL DEFAULT 1,
      created_at TEXT NOT NULL
    );
    CREATE TABLE IF NOT EXISTS password_resets(
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      user_id INTEGER NOT NULL,
      token TEXT NOT NULL,
      created_at TEXT NOT NULL,
      confirmed INTEGER NOT NULL DEFAULT 0,
      used INTEGER NOT NULL DEFAULT 0,
      FOREIGN KEY(user_id) REFERENCES users(id)
    );
    CREATE TABLE IF NOT EXISTS jobs(
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      name TEXT NOT NULL,
      client TEXT,
      status TEXT NOT NULL DEFAULT 'nová',
      owner_id INTEGER NOT NULL,
      created_at TEXT NOT NULL,
      FOREIGN KEY(owner_id) REFERENCES users(id)
    );
    CREATE TABLE IF NOT EXISTS time_entries(
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      user_id INTEGER NOT NULL,
      job_id INTEGER,
      work_date TEXT NOT NULL,
      hours REAL NOT NULL,
      note TEXT,
      created_at TEXT NOT NULL,
      FOREIGN KEY(user_id) REFERENCES users(id),
      FOREIGN KEY(job_id) REFERENCES jobs(id)
    );
    CREATE TABLE IF NOT EXISTS stock_items(
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      name TEXT NOT NULL,
      qty REAL NOT NULL DEFAULT 0,
      unit TEXT DEFAULT 'ks',
      owner_id INTEGER NOT NULL,
      updated_at TEXT NOT NULL,
      FOREIGN KEY(owner_id) REFERENCES users(id)
    );
    """)
    db.commit()

def ensure_admin():
    db = get_db()
    admin_email = os.environ.get("ADMIN_EMAIL", "admin@example.com").strip().lower()
    admin_pass = os.environ.get("ADMIN_PASSWORD", "admin123")
    row = db.execute("SELECT id FROM users WHERE email=?", (admin_email,)).fetchone()
    if not row:
        db.execute("""INSERT INTO users(email,name,role,password_hash,approved,active,created_at)
                      VALUES (?,?,?,?,1,1,?)""",
                   (admin_email, "Admin", "admin", generate_password_hash(admin_pass), datetime.utcnow().isoformat()))
        db.commit()

@app.before_first_request
def bootstrap():
    init_db(); ensure_admin()

def current_user():
    uid = session.get("uid")
    if not uid: return None
    row = get_db().execute("SELECT id,email,name,role,approved,active FROM users WHERE id=?", (uid,)).fetchone()
    return dict(row) if row else None

def login_required():
    u = current_user()
    if not u or not u["approved"] or not u["active"]:
        return None, redirect("/login")
    return u, None

def admin_required():
    u, err = login_required()
    if err: return None, err
    if u["role"] != "admin":
        return None, Response("forbidden", 403)
    return u, None

@app.after_request
def sec_headers(resp):
    resp.headers.setdefault("X-Content-Type-Options","nosniff")
    resp.headers.setdefault("X-Frame-Options","DENY")
    resp.headers.setdefault("Referrer-Policy","no-referrer")
    resp.headers.setdefault("Content-Security-Policy","default-src 'self'; img-src 'self' data:; style-src 'self' 'unsafe-inline'; script-src 'self' 'unsafe-inline';")
    return resp

@app.route("/", endpoint="root")
def root():
    u = current_user()
    return redirect("/login") if not u else redirect("/dashboard")

@app.route("/login", methods=["GET","POST"])
def login_page():
    if request.method == "GET": return render_template("login.html", title="Přihlášení")
    email = (request.form.get("email") or "").strip().lower()
    password = request.form.get("password") or ""
    db = get_db()
    row = db.execute("SELECT id,password_hash,approved,active FROM users WHERE email=?", (email,)).fetchone()
    if not row or not check_password_hash(row["password_hash"], password) or not row["active"]:
        flash("Neplatné přihlašovací údaje", "error"); return redirect("/login")
    if not row["approved"]:
        flash("Účet čeká na schválení administrátorem.", "error"); return redirect("/login")
    session["uid"] = row["id"]; flash("Přihlášeno.", "success"); return redirect("/dashboard")

@app.route("/logout")
def logout():
    session.clear(); flash("Odhlášeno.", "success"); return redirect("/login")

@app.route("/register", methods=["GET","POST"])
def register_page():
    if request.method == "GET": return render_template("register.html", title="Registrace")
    email = (request.form.get("email") or "").strip().lower()
    password = request.form.get("password") or ""
    name = (request.form.get("name") or "").strip() or None
    if not email or not password: 
        flash("Vyplňte e-mail i heslo.", "error"); return redirect("/register")
    db = get_db()
    if db.execute("SELECT 1 FROM users WHERE email=?", (email,)).fetchone():
        flash("Účet s tímto e-mailem už existuje.", "error"); return redirect("/register")
    db.execute("""INSERT INTO users(email,name,role,password_hash,approved,active,created_at)
                  VALUES (?,?,?,?,0,1,?)""",
               (email, name, "user", generate_password_hash(password), datetime.utcnow().isoformat()))
    db.commit(); flash("Registrace odeslána. Počkejte na schválení adminem.", "success"); return redirect("/login")

@app.route("/forgot", methods=["GET","POST"])
def forgot_page():
    if request.method == "GET": return render_template("forgot.html", title="Zapomenuté heslo")
    email = (request.form.get("email") or "").strip().lower()
    db = get_db(); u = db.execute("SELECT id FROM users WHERE email=?", (email,)).fetchone()
    if u:
        token = secrets.token_urlsafe(32)
        db.execute("INSERT INTO password_resets(user_id,token,created_at,confirmed,used) VALUES (?,?,?,?,0)",
                   (u["id"], token, datetime.utcnow().isoformat(), 0)); db.commit()
    flash("Pokud účet existuje, byla vytvořena žádost o reset (čeká na schválení).", "success"); return redirect("/login")

@app.route("/reset/<token>", methods=["GET","POST"])
def reset_page(token):
    db = get_db()
    row = db.execute("SELECT id,user_id,confirmed,used FROM password_resets WHERE token=?", (token,)).fetchone()
    if request.method == "GET":
        return render_template("reset.html", title="Reset hesla", allowed=bool(row and row["confirmed"] and not row["used"]), token=token)
    new_pass = request.form.get("password") or ""
    if not row or not row["confirmed"] or row["used"]:
        flash("Tento resetový odkaz není platný.", "error"); return redirect("/login")
    db.execute("UPDATE users SET password_hash=? WHERE id=?", (generate_password_hash(new_pass), row["user_id"]))
    db.execute("UPDATE password_resets SET used=1 WHERE id=?", (row["id"],)); db.commit()
    flash("Heslo změněno. Přihlaste se.", "success"); return redirect("/login")

@app.route("/dashboard")
def dashboard_page():
    u, err = login_required()
    if err: return err
    db = get_db()
    hours = db.execute("""
        SELECT t.id, t.work_date, t.hours, t.note, j.name AS job_name
        FROM time_entries t LEFT JOIN jobs j ON j.id=t.job_id
        WHERE t.user_id=? ORDER BY t.work_date DESC, t.id DESC LIMIT 10
    """, (u["id"],)).fetchall()
    jobs = db.execute("""
        SELECT id,name,client,status FROM jobs
        WHERE owner_id=? ORDER BY id DESC LIMIT 10
    """, (u["id"],)).fetchall()
    return render_template("dashboard.html", title="Dashboard", user=u, hours=hours, jobs=jobs)

@app.route("/jobs")
def jobs_list():
    u, err = login_required()
    if err: return err
    db = get_db()
    if u["role"] == "admin":
        rows = db.execute("SELECT j.*, u.email AS owner_email FROM jobs j JOIN users u ON u.id=j.owner_id ORDER BY j.id DESC").fetchall()
    else:
        rows = db.execute("SELECT j.*, u.email AS owner_email FROM jobs j JOIN users u ON u.id=j.owner_id WHERE j.owner_id=? ORDER BY j.id DESC", (u["id"],)).fetchall()
    return render_template("jobs_list.html", title="Zakázky", rows=rows, user=u)

@app.route("/jobs/new", methods=["GET","POST"])
def jobs_new():
    u, err = login_required()
    if err: return err
    if request.method == "GET":
        return render_template("jobs_edit.html", title="Nová zakázka", item=None)
    name = (request.form.get("name") or "").strip()
    client = (request.form.get("client") or "").strip() or None
    status = (request.form.get("status") or "nová").strip()
    if not name:
        flash("Název je povinný.", "error"); return redirect("/jobs/new")
    db = get_db()
    db.execute("INSERT INTO jobs(name,client,status,owner_id,created_at) VALUES (?,?,?,?,?)",
               (name, client, status, u["id"], datetime.utcnow().isoformat()))
    db.commit(); flash("Zakázka vytvořena.", "success"); return redirect("/jobs")

@app.route("/jobs/<int:jid>/edit", methods=["GET","POST"])
def jobs_edit(jid):
    u, err = login_required()
    if err: return err
    db = get_db()
    item = db.execute("SELECT * FROM jobs WHERE id=?", (jid,)).fetchone()
    if not item: return Response("not found", 404)
    if u["role"] != "admin" and item["owner_id"] != u["id"]:
        return Response("forbidden", 403)
    if request.method == "GET":
        return render_template("jobs_edit.html", title="Upravit zakázku", item=item)
    name = (request.form.get("name") or "").strip()
    client = (request.form.get("client") or "").strip() or None
    status = (request.form.get("status") or "nová").strip()
    db.execute("UPDATE jobs SET name=?, client=?, status=? WHERE id=?", (name, client, status, jid))
    db.commit(); flash("Zakázka uložena.", "success"); return redirect("/jobs")

@app.route("/jobs/<int:jid>/delete", methods=["POST"])
def jobs_delete(jid):
    u, err = login_required()
    if err: return err
    db = get_db()
    item = db.execute("SELECT owner_id FROM jobs WHERE id=?", (jid,)).fetchone()
    if not item: return Response("not found", 404)
    if u["role"] != "admin" and item["owner_id"] != u["id"]:
        return Response("forbidden", 403)
    db.execute("DELETE FROM jobs WHERE id=?", (jid,)); db.commit()
    flash("Zakázka smazána.", "success"); return redirect("/jobs")

@app.route("/time")
def time_list():
    u, err = login_required()
    if err: return err
    db = get_db()
    if u["role"] == "admin":
        rows = db.execute("""
            SELECT t.*, u.email AS user_email, j.name AS job_name FROM time_entries t
            JOIN users u ON u.id=t.user_id
            LEFT JOIN jobs j ON j.id=t.job_id
            ORDER BY t.work_date DESC, t.id DESC LIMIT 200
        """).fetchall()
    else:
        rows = db.execute("""
            SELECT t.*, j.name AS job_name FROM time_entries t
            LEFT JOIN jobs j ON j.id=t.job_id
            WHERE t.user_id=? ORDER BY t.work_date DESC, t.id DESC LIMIT 200
        """, (u["id"],)).fetchall()
    jobs = db.execute("SELECT id,name FROM jobs WHERE owner_id=? OR ?='admin'", (u["id"], u["role"])).fetchall()
    return render_template("time_list.html", title="Hodiny", rows=rows, jobs=jobs, user=u)

@app.route("/time/new", methods=["POST"])
def time_new():
    u, err = login_required()
    if err: return err
    db = get_db()
    job_id = request.form.get("job_id")
    work_date = (request.form.get("work_date") or date.today().isoformat())
    hours = float(request.form.get("hours") or 0)
    note = (request.form.get("note") or "").strip() or None
    db.execute("INSERT INTO time_entries(user_id,job_id,work_date,hours,note,created_at) VALUES (?,?,?,?,?,?)",
               (u["id"], job_id or None, work_date, hours, note, datetime.utcnow().isoformat()))
    db.commit(); flash("Záznam přidán.", "success"); return redirect("/time")

@app.route("/time/<int:tid>/delete", methods=["POST"])
def time_delete(tid):
    u, err = login_required()
    if err: return err
    db = get_db()
    row = db.execute("SELECT user_id FROM time_entries WHERE id=?", (tid,)).fetchone()
    if not row: return Response("not found", 404)
    if u["role"] != "admin" and row["user_id"] != u["id"]:
        return Response("forbidden", 403)
    db.execute("DELETE FROM time_entries WHERE id=?", (tid,)); db.commit()
    flash("Záznam smazán.", "success"); return redirect("/time")

@app.route("/stock")
def stock_list():
    u, err = login_required()
    if err: return err
    db = get_db()
    if u["role"] == "admin":
        rows = db.execute("SELECT s.*, u.email as owner_email FROM stock_items s JOIN users u ON u.id=s.owner_id ORDER BY s.id DESC").fetchall()
    else:
        rows = db.execute("SELECT * FROM stock_items WHERE owner_id=? ORDER BY id DESC", (u["id"],)).fetchall()
    return render_template("stock_list.html", title="Sklad", rows=rows, user=u)

@app.route("/stock/new", methods=["POST"])
def stock_new():
    u, err = login_required()
    if err: return err
    name = (request.form.get("name") or "").strip()
    qty = float(request.form.get("qty") or 0)
    unit = (request.form.get("unit") or "ks").strip()
    if not name:
        flash("Název je povinný.", "error"); return redirect("/stock")
    db = get_db()
    db.execute("INSERT INTO stock_items(name,qty,unit,owner_id,updated_at) VALUES (?,?,?,?,?)",
               (name, qty, unit, u["id"], datetime.utcnow().isoformat()))
    db.commit(); flash("Položka uložena.", "success"); return redirect("/stock")

@app.route("/stock/<int:sid>/delete", methods=["POST"])
def stock_delete(sid):
    u, err = login_required()
    if err: return err
    db = get_db()
    row = db.execute("SELECT owner_id FROM stock_items WHERE id=?", (sid,)).fetchone()
    if not row: return Response("not found", 404)
    if u["role"] != "admin" and row["owner_id"] != u["id"]:
        return Response("forbidden", 403)
    db.execute("DELETE FROM stock_items WHERE id=?", (sid,)); db.commit()
    flash("Položka smazána.", "success"); return redirect("/stock")

@app.route("/export/xlsx")
def export_xlsx():
    u, err = login_required()
    if err: return err
    db = get_db()
    if u["role"] == "admin":
        rows = db.execute("""
            SELECT t.id, u.email, t.work_date, t.hours, t.note, j.name as job_name
            FROM time_entries t JOIN users u ON u.id=t.user_id
            LEFT JOIN jobs j ON j.id=t.job_id
            ORDER BY t.work_date ASC
        """).fetchall()
    else:
        rows = db.execute("""
            SELECT t.id, ? as email, t.work_date, t.hours, t.note, j.name as job_name
            FROM time_entries t LEFT JOIN jobs j ON j.id=t.job_id
            WHERE t.user_id=? ORDER BY t.work_date ASC
        """, (u["email"], u["id"])).fetchall()
    try:
        import openpyxl
    except Exception:
        return Response("openpyxl missing", 500)
    wb = openpyxl.Workbook()
    ws = wb.active; ws.title = "Hodiny"
    ws.append(["ID","Uživatel","Datum","Hodiny","Zakázka","Poznámka"])
    for r in rows:
        ws.append([r["id"], r["email"], r["work_date"], float(r["hours"]), r["job_name"] or "", r["note"] or ""])
    buf = io.BytesIO(); wb.save(buf); buf.seek(0)
    fname = f"export_{datetime.utcnow().strftime('%Y%m%d_%H%M')}.xlsx"
    return send_file(buf, mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                     as_attachment=True, download_name=fname)

@app.route("/admin/users", methods=["GET","POST"])
def admin_users():
    u, err = admin_required()
    if err: return err
    db = get_db()
    if request.method == "GET":
        users = [dict(r) for r in db.execute("SELECT id,email,name,role,approved,active,created_at FROM users ORDER BY id DESC")]
        return render_template("admin_users.html", title="Uživatelé", users=users)
    act = request.form.get("action"); uid = int(request.form.get("id") or 0)
    if act == "approve": db.execute("UPDATE users SET approved=1 WHERE id=?", (uid,))
    elif act == "disable": db.execute("UPDATE users SET active=0 WHERE id=?", (uid,))
    elif act == "enable": db.execute("UPDATE users SET active=1 WHERE id=?", (uid,))
    elif act == "make_admin": db.execute("UPDATE users SET role='admin' WHERE id=?", (uid,))
    db.commit(); return redirect("/admin/users")

@app.route("/admin/resets", methods=["GET","POST","DELETE"])
def admin_resets():
    u, err = admin_required()
    if err: return err
    db = get_db()
    if request.method == "GET":
        items = [dict(r) for r in db.execute("""
            SELECT pr.id, pr.token, pr.confirmed, pr.used, pr.created_at, u.email
            FROM password_resets pr JOIN users u ON u.id=pr.user_id
            ORDER BY pr.id DESC
        """)]
        return render_template("admin_resets.html", title="Resety hesel", items=items)
    if request.method == "POST":
        rid = int(request.form.get("id") or 0)
        db.execute("UPDATE password_resets SET confirmed=1 WHERE id=?", (rid,)); db.commit()
        return redirect("/admin/resets")
    rid = int(request.args.get("id") or 0)
    db.execute("DELETE FROM password_resets WHERE id=?", (rid,)); db.commit()
    return redirect("/admin/resets")

@app.route("/healthz")
def healthz():
    try:
        get_db().execute("SELECT 1").fetchone()
        return jsonify(ok=True)
    except Exception as e:
        return jsonify(ok=False, error=str(e)), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
