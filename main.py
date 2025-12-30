"""
Green David App - Opravená verze
Firemní systém pro správu zakázek, zaměstnanců a výkazů hodin
"""
import os
import re
import io
import sqlite3
import logging
from datetime import datetime, date, timedelta
from functools import wraps
from flask import Flask, abort, g, jsonify, render_template, request, send_file, send_from_directory, session, redirect
from werkzeug.security import generate_password_hash, check_password_hash

# ============================================================================
# KONFIGURACE
# ============================================================================

# Načtení konfigurace z prostředí
DB_PATH = os.environ.get("DB_PATH", "app.db")
UPLOAD_DIR = os.environ.get("UPLOAD_DIR", "uploads")

# BEZPEČNOST: SECRET_KEY musí být nastaven v produkci
SECRET_KEY = os.environ.get("SECRET_KEY")
if not SECRET_KEY:
    if os.environ.get("FLASK_ENV") == "production":
        raise ValueError("SECRET_KEY must be set in production!")
    SECRET_KEY = "dev-unsafe-key-change-me"
    logging.warning("Using default SECRET_KEY - NOT FOR PRODUCTION!")

# Logging konfigurace
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('app.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# ============================================================================
# FLASK APLIKACE
# ============================================================================

app = Flask(__name__, static_folder=".", static_url_path="")
app.secret_key = SECRET_KEY
app.config.update(
    SESSION_COOKIE_SECURE=os.environ.get("FLASK_ENV") == "production",
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE='Lax',
    PERMANENT_SESSION_LIFETIME=timedelta(hours=24)
)

os.makedirs(UPLOAD_DIR, exist_ok=True)

# ============================================================================
# DATABÁZOVÉ UTILITY
# ============================================================================

def _normalize_date(v):
    """Normalizuje datum do formátu YYYY-MM-DD"""
    if not v:
        return v
    s = str(v).strip()
    
    # Už je v ISO formátu
    m = re.match(r"^(\d{4})-(\d{1,2})-(\d{1,2})$", s)
    if m:
        y, M, d = m.groups()
        return f"{int(y):04d}-{int(M):02d}-{int(d):02d}"
    
    # Český formát DD.MM.YYYY
    m = re.match(r"^(\d{1,2})[\.\s-](\d{1,2})[\.\s-](\d{4})$", s)
    if m:
        d, M, y = m.groups()
        return f"{int(y):04d}-{int(M):02d}-{int(d):02d}"
    
    return s


def get_db():
    """Získá databázové připojení pro aktuální request"""
    if "db" not in g:
        g.db = sqlite3.connect(DB_PATH)
        g.db.row_factory = sqlite3.Row
    return g.db


@app.teardown_appcontext
def close_db(error=None):
    """Uzavře databázové připojení na konci requestu"""
    db = g.pop("db", None)
    if db is not None:
        db.close()


# ============================================================================
# AUTENTIZACE A AUTORIZACE
# ============================================================================

def current_user():
    """Vrátí aktuálně přihlášeného uživatele"""
    uid = session.get("uid")
    if not uid:
        return None
    
    db = get_db()
    row = db.execute(
        "SELECT id, email, name, role, active FROM users WHERE id=?",
        (uid,)
    ).fetchone()
    
    return dict(row) if row else None


def require_auth():
    """Vyžaduje přihlášeného uživatele"""
    u = current_user()
    if not u or not u.get("active"):
        return None, (jsonify({"ok": False, "error": "unauthorized"}), 401)
    return u, None


def require_role(write=False):
    """Vyžaduje specifickou roli (manager/admin pro write operace)"""
    u, err = require_auth()
    if err:
        return None, err
    
    if write and u["role"] not in ("admin", "manager"):
        logger.warning(f"User {u['email']} attempted write operation without permission")
        return None, (jsonify({"ok": False, "error": "forbidden"}), 403)
    
    return u, None


def login_required(f):
    """Dekorátor pro view funkce vyžadující přihlášení"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user():
            return redirect('/login')
        return f(*args, **kwargs)
    return decorated_function


# ============================================================================
# INICIALIZACE DATABÁZE
# ============================================================================

def ensure_schema():
    """Vytvoří databázové schéma pokud neexistuje"""
    db = get_db()
    _do_ensure_schema(db)


def _do_ensure_schema(db):
    """Interní funkce pro vytvoření schématu"""
    
    # Uživatelé
    db.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            role TEXT NOT NULL CHECK(role IN ('admin','manager','worker')),
            password_hash TEXT NOT NULL,
            active INTEGER NOT NULL DEFAULT 1,
            created_at TEXT NOT NULL DEFAULT (datetime('now'))
        )
    """)
    
    # Zaměstnanci
    db.execute("""
        CREATE TABLE IF NOT EXISTS employees (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            role TEXT NOT NULL DEFAULT 'worker'
        )
    """)
    
    # Zakázky
    db.execute("""
        CREATE TABLE IF NOT EXISTS jobs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            client TEXT NOT NULL DEFAULT '',
            status TEXT NOT NULL DEFAULT 'Plán',
            city TEXT NOT NULL DEFAULT '',
            code TEXT NOT NULL DEFAULT '',
            date TEXT,
            note TEXT,
            completed_at TEXT,
            created_at TEXT NOT NULL DEFAULT (datetime('now')),
            updated_at TEXT NOT NULL DEFAULT (datetime('now'))
        )
    """)
    
    # Přiřazení zaměstnanců k zakázkám
    db.execute("""
        CREATE TABLE IF NOT EXISTS job_assignments (
            job_id INTEGER NOT NULL,
            employee_id INTEGER NOT NULL,
            PRIMARY KEY (job_id, employee_id),
            FOREIGN KEY (job_id) REFERENCES jobs(id) ON DELETE CASCADE,
            FOREIGN KEY (employee_id) REFERENCES employees(id) ON DELETE CASCADE
        )
    """)
    
    # Materiál k zakázkám
    db.execute("""
        CREATE TABLE IF NOT EXISTS job_materials (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            job_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            qty REAL NOT NULL DEFAULT 0,
            unit TEXT NOT NULL DEFAULT 'ks',
            FOREIGN KEY (job_id) REFERENCES jobs(id) ON DELETE CASCADE
        )
    """)
    
    # Nářadí k zakázkám
    db.execute("""
        CREATE TABLE IF NOT EXISTS job_tools (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            job_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            qty REAL NOT NULL DEFAULT 0,
            unit TEXT NOT NULL DEFAULT 'ks',
            FOREIGN KEY (job_id) REFERENCES jobs(id) ON DELETE CASCADE
        )
    """)
    
    # Úkoly
    db.execute("""
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            job_id INTEGER,
            employee_id INTEGER,
            title TEXT NOT NULL,
            description TEXT DEFAULT '',
            status TEXT NOT NULL DEFAULT 'open',
            due_date TEXT,
            created_at TEXT NOT NULL DEFAULT (datetime('now')),
            FOREIGN KEY (job_id) REFERENCES jobs(id) ON DELETE SET NULL,
            FOREIGN KEY (employee_id) REFERENCES employees(id) ON DELETE SET NULL
        )
    """)
    
    # Výkazy hodin
    db.execute("""
        CREATE TABLE IF NOT EXISTS timesheets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            employee_id INTEGER NOT NULL,
            job_id INTEGER NOT NULL,
            date TEXT NOT NULL,
            hours REAL NOT NULL DEFAULT 0,
            place TEXT DEFAULT '',
            activity TEXT DEFAULT '',
            created_at TEXT NOT NULL DEFAULT (datetime('now')),
            FOREIGN KEY (employee_id) REFERENCES employees(id) ON DELETE CASCADE,
            FOREIGN KEY (job_id) REFERENCES jobs(id) ON DELETE CASCADE
        )
    """)
    
    # Kalendářové události
    db.execute("""
        CREATE TABLE IF NOT EXISTS calendar_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT NOT NULL,
            title TEXT NOT NULL,
            kind TEXT NOT NULL DEFAULT 'note',
            job_id INTEGER,
            start_time TEXT,
            end_time TEXT,
            note TEXT DEFAULT '',
            color TEXT DEFAULT '#2e7d32',
            created_at TEXT NOT NULL DEFAULT (datetime('now')),
            FOREIGN KEY (job_id) REFERENCES jobs(id) ON DELETE SET NULL
        )
    """)
    
    # Indexy pro výkon
    db.execute("CREATE INDEX IF NOT EXISTS idx_jobs_date ON jobs(date)")
    db.execute("CREATE INDEX IF NOT EXISTS idx_jobs_status ON jobs(status)")
    db.execute("CREATE INDEX IF NOT EXISTS idx_timesheets_date ON timesheets(date)")
    db.execute("CREATE INDEX IF NOT EXISTS idx_timesheets_employee ON timesheets(employee_id)")
    db.execute("CREATE INDEX IF NOT EXISTS idx_timesheets_job ON timesheets(job_id)")
    db.execute("CREATE INDEX IF NOT EXISTS idx_calendar_date ON calendar_events(date)")
    
    db.commit()
    logger.info("Database schema initialized")


def seed_admin():
    """Vytvoří výchozího admin uživatele pokud neexistují žádní uživatelé"""
    db = get_db()
    cur = db.execute("SELECT COUNT(*) c FROM users")
    
    if cur.fetchone()["c"] == 0:
        admin_email = os.environ.get("ADMIN_EMAIL", "admin@greendavid.local")
        admin_name = os.environ.get("ADMIN_NAME", "Admin")
        admin_password = os.environ.get("ADMIN_PASSWORD", "admin123")
        
        # BEZPEČNOST: Varování pokud používáme výchozí heslo
        if admin_password == "admin123":
            logger.warning("Using default admin password - CHANGE IT IMMEDIATELY!")
        
        db.execute(
            "INSERT INTO users(email, name, role, password_hash, active, created_at) VALUES (?,?,?,?,1,?)",
            (
                admin_email,
                admin_name,
                "admin",
                generate_password_hash(admin_password),
                datetime.utcnow().isoformat()
            )
        )
        db.commit()
        logger.info(f"Admin user created: {admin_email}")


@app.before_request
def _ensure_setup():
    """Zajistí inicializaci databáze před každým requestem"""
    ensure_schema()
    seed_admin()


# ============================================================================
# VALIDAČNÍ FUNKCE
# ============================================================================

def validate_hours(hours):
    """Validuje počet hodin"""
    try:
        h = float(hours)
        if h < 0 or h > 24:
            return False, "Hodiny musí být mezi 0 a 24"
        return True, h
    except (ValueError, TypeError):
        return False, "Neplatná hodnota hodin"


def validate_email(email):
    """Validuje email"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if not re.match(pattern, email):
        return False, "Neplatný formát emailu"
    return True, email.lower()


def sanitize_filename(filename):
    """Sanitizuje název souboru a odstraní path traversal"""
    # Odstranit path separátory a parent odkazy
    name = os.path.basename(filename)  # Vezme jen jméno souboru
    # Nahradit nebezpečné znaky
    name = re.sub(r"[^a-zA-Z0-9._-]", "_", name)
    # Odstranit počáteční tečky (hidden files)
    name = name.lstrip('.')
    return name or "unnamed"


# ============================================================================
# STATICKÉ SOUBORY
# ============================================================================

@app.route("/")
def index():
    return send_from_directory(".", "index.html")


@app.route("/uploads/<path:name>")
def uploaded_file(name):
    safe = sanitize_filename(name)
    path = os.path.join(UPLOAD_DIR, safe)
    
    if not os.path.isfile(path):
        abort(404)
    
    return send_from_directory(UPLOAD_DIR, safe)


@app.route("/health")
def health():
    """Health check endpoint"""
    try:
        db = get_db()
        db.execute("SELECT 1").fetchone()
        return jsonify({"status": "ok", "timestamp": datetime.utcnow().isoformat()})
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return jsonify({"status": "error", "error": str(e)}), 500


# ============================================================================
# API - AUTENTIZACE
# ============================================================================

@app.route("/api/me")
def api_me():
    """Vrátí informace o aktuálním uživateli"""
    u = current_user()
    tasks_count = 0
    
    if u:
        try:
            db = get_db()
            tasks_count = db.execute(
                "SELECT COUNT(*) c FROM tasks WHERE employee_id=? AND status!='hotovo'",
                (u["id"],)
            ).fetchone()["c"]
        except Exception as e:
            logger.error(f"Error counting tasks: {e}")
    
    return jsonify({
        "ok": True,
        "authenticated": bool(u),
        "user": u,
        "tasks_count": tasks_count
    })


@app.route("/api/login", methods=["POST"])
def api_login():
    """Přihlášení uživatele"""
    data = request.get_json(force=True, silent=True) or {}
    
    # Validace emailu
    email = (data.get("email") or "").strip().lower()
    valid, result = validate_email(email)
    if not valid:
        logger.warning(f"Invalid email format: {email}")
        return jsonify({"ok": False, "error": "invalid_email"}), 400
    
    email = result
    password = data.get("password") or ""
    
    db = get_db()
    row = db.execute(
        "SELECT id, email, name, role, password_hash, active FROM users WHERE email=?",
        (email,)
    ).fetchone()
    
    if not row or not check_password_hash(row["password_hash"], password) or not row["active"]:
        logger.warning(f"Failed login attempt for: {email}")
        return jsonify({"ok": False, "error": "invalid_credentials"}), 401
    
    session["uid"] = row["id"]
    session.permanent = True
    
    logger.info(f"User logged in: {email}")
    return jsonify({"ok": True})


@app.route("/api/logout", methods=["POST"])
def api_logout():
    """Odhlášení uživatele"""
    email = None
    u = current_user()
    if u:
        email = u.get("email")
    
    session.pop("uid", None)
    
    if email:
        logger.info(f"User logged out: {email}")
    
    return jsonify({"ok": True})


# ============================================================================
# API - ZAMĚSTNANCI
# ============================================================================

@app.route("/api/employees", methods=["GET", "POST", "PATCH", "DELETE"])
def api_employees():
    """CRUD operace se zaměstnanci"""
    u, err = require_role(write=(request.method != "GET"))
    if err:
        return err
    
    db = get_db()
    
    if request.method == "GET":
        try:
            rows = db.execute(
                "SELECT * FROM employees ORDER BY name ASC"
            ).fetchall()
            return jsonify({"ok": True, "employees": [dict(r) for r in rows]})
        except Exception as e:
            logger.error(f"Error fetching employees: {e}")
            return jsonify({"ok": False, "error": "database_error"}), 500
    
    if request.method == "POST":
        data = request.get_json(force=True, silent=True) or {}
        name = (data.get("name") or "").strip()
        role = (data.get("role") or "worker").strip()
        
        if not name:
            return jsonify({"ok": False, "error": "missing_name"}), 400
        
        try:
            db.execute(
                "INSERT INTO employees(name, role) VALUES (?, ?)",
                (name, role)
            )
            db.commit()
            logger.info(f"Employee created: {name}")
            return jsonify({"ok": True})
        except Exception as e:
            logger.error(f"Error creating employee: {e}")
            db.rollback()
            return jsonify({"ok": False, "error": "database_error"}), 500
    
    if request.method == "PATCH":
        data = request.get_json(force=True, silent=True) or {}
        eid = data.get("id")
        
        if not eid:
            return jsonify({"ok": False, "error": "missing_id"}), 400
        
        updates = []
        params = []
        
        if "name" in data:
            updates.append("name=?")
            params.append(data["name"].strip())
        
        if "role" in data:
            updates.append("role=?")
            params.append(data["role"].strip())
        
        if not updates:
            return jsonify({"ok": False, "error": "nothing_to_update"}), 400
        
        params.append(int(eid))
        
        try:
            db.execute(
                f"UPDATE employees SET {', '.join(updates)} WHERE id=?",
                params
            )
            db.commit()
            logger.info(f"Employee updated: ID {eid}")
            return jsonify({"ok": True})
        except Exception as e:
            logger.error(f"Error updating employee: {e}")
            db.rollback()
            return jsonify({"ok": False, "error": "database_error"}), 500
    
    if request.method == "DELETE":
        eid = request.args.get("id", type=int)
        
        if not eid:
            return jsonify({"ok": False, "error": "missing_id"}), 400
        
        try:
            db.execute("DELETE FROM employees WHERE id=?", (eid,))
            db.commit()
            logger.info(f"Employee deleted: ID {eid}")
            return jsonify({"ok": True})
        except Exception as e:
            logger.error(f"Error deleting employee: {e}")
            db.rollback()
            return jsonify({"ok": False, "error": "database_error"}), 500


# ============================================================================
# API - ZAKÁZKY
# ============================================================================

@app.route("/api/jobs", methods=["GET", "POST", "PATCH", "DELETE"])
def api_jobs():
    """CRUD operace se zakázkami"""
    u, err = require_role(write=(request.method != "GET"))
    if err:
        return err
    
    db = get_db()
    
    if request.method == "GET":
        try:
            rows = db.execute("""
                SELECT * FROM jobs 
                WHERE LOWER(status) NOT LIKE 'dokon%'
                ORDER BY date(date) DESC, id DESC
            """).fetchall()
            
            result = []
            for r in rows:
                job = dict(r)
                if job.get("date"):
                    job["date"] = _normalize_date(job["date"])
                result.append(job)
            
            return jsonify({"ok": True, "jobs": result})
        except Exception as e:
            logger.error(f"Error fetching jobs: {e}")
            return jsonify({"ok": False, "error": "database_error"}), 500
    
    if request.method == "POST":
        data = request.get_json(force=True, silent=True) or {}
        
        title = (data.get("title") or "").strip()
        client = (data.get("client") or "").strip()
        status = (data.get("status") or "Plán").strip()
        city = (data.get("city") or "").strip()
        code = (data.get("code") or "").strip()
        note = data.get("note") or ""
        dt = _normalize_date(data.get("date"))
        
        # Validace povinných polí
        required = [title, city, code, dt]
        if not all(v for v in required):
            return jsonify({"ok": False, "error": "missing_required_fields"}), 400
        
        try:
            db.execute("""
                INSERT INTO jobs(title, client, status, city, code, date, note, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, datetime('now'), datetime('now'))
            """, (title, client, status, city, code, dt, note))
            db.commit()
            
            logger.info(f"Job created: {title} ({code})")
            return jsonify({"ok": True})
        except Exception as e:
            logger.error(f"Error creating job: {e}")
            db.rollback()
            return jsonify({"ok": False, "error": "database_error"}), 500
    
    if request.method == "PATCH":
        data = request.get_json(force=True, silent=True) or {}
        jid = data.get("id")
        
        if not jid:
            return jsonify({"ok": False, "error": "missing_id"}), 400
        
        updates = []
        params = []
        
        for field in ["title", "client", "status", "city", "code", "note"]:
            if field in data:
                updates.append(f"{field}=?")
                params.append(data[field])
        
        if "date" in data:
            updates.append("date=?")
            params.append(_normalize_date(data["date"]))
        
        if not updates:
            return jsonify({"ok": False, "error": "nothing_to_update"}), 400
        
        # Vždy aktualizuj updated_at
        updates.append("updated_at=datetime('now')")
        params.append(int(jid))
        
        try:
            db.execute(
                f"UPDATE jobs SET {', '.join(updates)} WHERE id=?",
                params
            )
            db.commit()
            
            # Pokud je status Dokončeno, nastav completed_at
            if "status" in data:
                job = db.execute("SELECT status, completed_at FROM jobs WHERE id=?", (jid,)).fetchone()
                if job and job["status"].lower().startswith("dokon") and not job["completed_at"]:
                    db.execute(
                        "UPDATE jobs SET completed_at=date('now') WHERE id=?",
                        (jid,)
                    )
                    db.commit()
            
            logger.info(f"Job updated: ID {jid}")
            return jsonify({"ok": True})
        except Exception as e:
            logger.error(f"Error updating job: {e}")
            db.rollback()
            return jsonify({"ok": False, "error": "database_error"}), 500
    
    if request.method == "DELETE":
        jid = request.args.get("id", type=int)
        
        if not jid:
            return jsonify({"ok": False, "error": "missing_id"}), 400
        
        try:
            db.execute("DELETE FROM jobs WHERE id=?", (jid,))
            db.commit()
            logger.info(f"Job deleted: ID {jid}")
            return jsonify({"ok": True})
        except Exception as e:
            logger.error(f"Error deleting job: {e}")
            db.rollback()
            return jsonify({"ok": False, "error": "database_error"}), 500


# ============================================================================
# API - VÝKAZY HODIN
# ============================================================================

@app.route("/api/timesheets", methods=["GET", "POST", "PATCH", "DELETE"])
def api_timesheets():
    """CRUD operace s výkazy hodin"""
    u, err = require_role(write=(request.method != "GET"))
    if err:
        return err
    
    db = get_db()
    
    if request.method == "GET":
        emp = request.args.get("employee_id", type=int)
        jid = request.args.get("job_id", type=int)
        d_from = _normalize_date(request.args.get("from"))
        d_to = _normalize_date(request.args.get("to"))
        
        query = """
            SELECT t.id, t.employee_id, t.job_id, t.date, t.hours, t.place, t.activity,
                   e.name AS employee_name, j.title AS job_title, j.code AS job_code
            FROM timesheets t
            LEFT JOIN employees e ON e.id = t.employee_id
            LEFT JOIN jobs j ON j.id = t.job_id
        """
        
        conditions = []
        params = []
        
        if emp:
            conditions.append("t.employee_id=?")
            params.append(emp)
        
        if jid:
            conditions.append("t.job_id=?")
            params.append(jid)
        
        if d_from and d_to:
            conditions.append("date(t.date) BETWEEN date(?) AND date(?)")
            params.extend([d_from, d_to])
        elif d_from:
            conditions.append("date(t.date) >= date(?)")
            params.append(d_from)
        elif d_to:
            conditions.append("date(t.date) <= date(?)")
            params.append(d_to)
        
        if conditions:
            query += " WHERE " + " AND ".join(conditions)
        
        query += " ORDER BY t.date ASC, t.id ASC"
        
        try:
            rows = db.execute(query, params).fetchall()
            return jsonify({"ok": True, "rows": [dict(r) for r in rows]})
        except Exception as e:
            logger.error(f"Error fetching timesheets: {e}")
            return jsonify({"ok": False, "error": "database_error"}), 500
    
    if request.method == "POST":
        data = request.get_json(force=True, silent=True) or {}
        
        emp = data.get("employee_id")
        job = data.get("job_id")
        dt = data.get("date")
        hours = data.get("hours")
        place = data.get("place") or ""
        activity = data.get("activity") or ""
        
        # Validace
        if not all([emp, job, dt, hours is not None]):
            return jsonify({"ok": False, "error": "missing_required_fields"}), 400
        
        valid, result = validate_hours(hours)
        if not valid:
            return jsonify({"ok": False, "error": result}), 400
        
        hours = result
        dt = _normalize_date(dt)
        
        try:
            db.execute("""
                INSERT INTO timesheets(employee_id, job_id, date, hours, place, activity, created_at)
                VALUES (?, ?, ?, ?, ?, ?, datetime('now'))
            """, (int(emp), int(job), dt, hours, place, activity))
            db.commit()
            
            logger.info(f"Timesheet created: Employee {emp}, Job {job}, {hours}h")
            return jsonify({"ok": True})
        except Exception as e:
            logger.error(f"Error creating timesheet: {e}")
            db.rollback()
            return jsonify({"ok": False, "error": "database_error"}), 500
    
    if request.method == "PATCH":
        data = request.get_json(force=True, silent=True) or {}
        tid = data.get("id")
        
        if not tid:
            return jsonify({"ok": False, "error": "missing_id"}), 400
        
        updates = []
        params = []
        
        for field in ["employee_id", "job_id", "place", "activity"]:
            if field in data:
                updates.append(f"{field}=?")
                val = data[field]
                if field in ["employee_id", "job_id"]:
                    val = int(val)
                params.append(val)
        
        if "date" in data:
            updates.append("date=?")
            params.append(_normalize_date(data["date"]))
        
        if "hours" in data:
            valid, result = validate_hours(data["hours"])
            if not valid:
                return jsonify({"ok": False, "error": result}), 400
            updates.append("hours=?")
            params.append(result)
        
        if not updates:
            return jsonify({"ok": False, "error": "nothing_to_update"}), 400
        
        params.append(int(tid))
        
        try:
            db.execute(
                f"UPDATE timesheets SET {', '.join(updates)} WHERE id=?",
                params
            )
            db.commit()
            logger.info(f"Timesheet updated: ID {tid}")
            return jsonify({"ok": True})
        except Exception as e:
            logger.error(f"Error updating timesheet: {e}")
            db.rollback()
            return jsonify({"ok": False, "error": "database_error"}), 500
    
    if request.method == "DELETE":
        tid = request.args.get("id", type=int)
        
        if not tid:
            return jsonify({"ok": False, "error": "missing_id"}), 400
        
        try:
            db.execute("DELETE FROM timesheets WHERE id=?", (tid,))
            db.commit()
            logger.info(f"Timesheet deleted: ID {tid}")
            return jsonify({"ok": True})
        except Exception as e:
            logger.error(f"Error deleting timesheet: {e}")
            db.rollback()
            return jsonify({"ok": False, "error": "database_error"}), 500


@app.route("/api/timesheets/export")
def api_timesheets_export():
    """Export výkazů do CSV"""
    u, err = require_role(write=False)
    if err:
        return err
    
    # Stejné filtry jako v GET
    emp = request.args.get("employee_id", type=int)
    jid = request.args.get("job_id", type=int)
    d_from = _normalize_date(request.args.get("from"))
    d_to = _normalize_date(request.args.get("to"))
    
    query = """
        SELECT t.id, t.date, t.hours, t.place, t.activity,
               e.id AS employee_id, e.name AS employee_name,
               j.id AS job_id, j.title AS job_title, j.code AS job_code
        FROM timesheets t
        LEFT JOIN employees e ON e.id = t.employee_id
        LEFT JOIN jobs j ON j.id = t.job_id
    """
    
    conditions = []
    params = []
    
    if emp:
        conditions.append("t.employee_id=?")
        params.append(emp)
    
    if jid:
        conditions.append("t.job_id=?")
        params.append(jid)
    
    if d_from and d_to:
        conditions.append("date(t.date) BETWEEN date(?) AND date(?)")
        params.extend([d_from, d_to])
    elif d_from:
        conditions.append("date(t.date) >= date(?)")
        params.append(d_from)
    elif d_to:
        conditions.append("date(t.date) <= date(?)")
        params.append(d_to)
    
    if conditions:
        query += " WHERE " + " AND ".join(conditions)
    
    query += " ORDER BY t.date ASC, t.id ASC"
    
    try:
        db = get_db()
        rows = db.execute(query, params).fetchall()
        
        output = io.StringIO()
        import csv
        writer = csv.writer(output)
        
        writer.writerow([
            "id", "date", "employee_id", "employee_name",
            "job_id", "job_title", "job_code", "hours", "place", "activity"
        ])
        
        for r in rows:
            writer.writerow([
                r["id"], r["date"], r["employee_id"], r["employee_name"] or "",
                r["job_id"], r["job_title"] or "", r["job_code"] or "",
                r["hours"], r["place"] or "", r["activity"] or ""
            ])
        
        mem = io.BytesIO(output.getvalue().encode("utf-8-sig"))
        mem.seek(0)
        
        return send_file(
            mem,
            mimetype="text/csv",
            as_attachment=True,
            download_name="timesheets.csv"
        )
    except Exception as e:
        logger.error(f"Error exporting timesheets: {e}")
        return jsonify({"ok": False, "error": "export_failed"}), 500


# ============================================================================
# API - ÚKOLY
# ============================================================================

@app.route("/api/tasks", methods=["GET", "POST", "PATCH", "DELETE"])
def api_tasks():
    """CRUD operace s úkoly"""
    u, err = require_role(write=(request.method != "GET"))
    if err:
        return err
    
    db = get_db()
    
    if request.method == "GET":
        jid = request.args.get("job_id", type=int)
        
        query = """
            SELECT t.id, t.job_id, t.employee_id, t.title, t.description, t.status, t.due_date,
                   e.name AS employee_name
            FROM tasks t
            LEFT JOIN employees e ON e.id = t.employee_id
        """
        
        params = []
        if jid:
            query += " WHERE t.job_id=?"
            params.append(jid)
        
        query += " ORDER BY COALESCE(t.due_date, '9999-12-31') ASC, t.id ASC"
        
        try:
            rows = db.execute(query, params).fetchall()
            return jsonify({"ok": True, "tasks": [dict(r) for r in rows]})
        except Exception as e:
            logger.error(f"Error fetching tasks: {e}")
            return jsonify({"ok": False, "error": "database_error"}), 500
    
    if request.method == "POST":
        data = request.get_json(force=True, silent=True) or {}
        
        title = (data.get("title") or "").strip()
        if not title:
            return jsonify({"ok": False, "error": "missing_title"}), 400
        
        description = (data.get("description") or "").strip()
        status = (data.get("status") or "open").strip()
        due_date = _normalize_date(data.get("due_date")) if data.get("due_date") else None
        employee_id = int(data["employee_id"]) if data.get("employee_id") else None
        job_id = int(data["job_id"]) if data.get("job_id") else None
        
        try:
            db.execute("""
                INSERT INTO tasks(job_id, employee_id, title, description, status, due_date, created_at)
                VALUES (?, ?, ?, ?, ?, ?, datetime('now'))
            """, (job_id, employee_id, title, description, status, due_date))
            db.commit()
            
            logger.info(f"Task created: {title}")
            return jsonify({"ok": True})
        except Exception as e:
            logger.error(f"Error creating task: {e}")
            db.rollback()
            return jsonify({"ok": False, "error": "database_error"}), 500
    
    if request.method == "PATCH":
        data = request.get_json(force=True, silent=True) or {}
        tid = data.get("id")
        
        if not tid:
            return jsonify({"ok": False, "error": "missing_id"}), 400
        
        updates = []
        params = []
        
        for field in ["title", "description", "status"]:
            if field in data:
                updates.append(f"{field}=?")
                params.append(data[field])
        
        if "due_date" in data:
            updates.append("due_date=?")
            params.append(_normalize_date(data["due_date"]) if data["due_date"] else None)
        
        if "employee_id" in data:
            updates.append("employee_id=?")
            params.append(int(data["employee_id"]) if data["employee_id"] else None)
        
        if "job_id" in data:
            updates.append("job_id=?")
            params.append(int(data["job_id"]) if data["job_id"] else None)
        
        if not updates:
            return jsonify({"ok": False, "error": "nothing_to_update"}), 400
        
        params.append(int(tid))
        
        try:
            db.execute(
                f"UPDATE tasks SET {', '.join(updates)} WHERE id=?",
                params
            )
            db.commit()
            logger.info(f"Task updated: ID {tid}")
            return jsonify({"ok": True})
        except Exception as e:
            logger.error(f"Error updating task: {e}")
            db.rollback()
            return jsonify({"ok": False, "error": "database_error"}), 500
    
    if request.method == "DELETE":
        tid = request.args.get("id", type=int)
        
        if not tid:
            return jsonify({"ok": False, "error": "missing_id"}), 400
        
        try:
            db.execute("DELETE FROM tasks WHERE id=?", (tid,))
            db.commit()
            logger.info(f"Task deleted: ID {tid}")
            return jsonify({"ok": True})
        except Exception as e:
            logger.error(f"Error deleting task: {e}")
            db.rollback()
            return jsonify({"ok": False, "error": "database_error"}), 500


# ============================================================================
# API - DETAILY ZAKÁZKY
# ============================================================================

@app.route("/api/jobs/<int:job_id>", methods=["GET"])
def api_job_detail(job_id):
    """Detail zakázky včetně materiálu, nářadí a přiřazení"""
    u, err = require_role(write=False)
    if err:
        return err
    
    db = get_db()
    
    try:
        job = db.execute("SELECT * FROM jobs WHERE id=?", (job_id,)).fetchone()
        if not job:
            return jsonify({"ok": False, "error": "not_found"}), 404
        
        job_dict = dict(job)
        if job_dict.get("date"):
            job_dict["date"] = _normalize_date(job_dict["date"])
        
        materials = [
            dict(r) for r in db.execute(
                "SELECT id, name, qty, unit FROM job_materials WHERE job_id=? ORDER BY id ASC",
                (job_id,)
            ).fetchall()
        ]
        
        tools = [
            dict(r) for r in db.execute(
                "SELECT id, name, qty, unit FROM job_tools WHERE job_id=? ORDER BY id ASC",
                (job_id,)
            ).fetchall()
        ]
        
        assignments = [
            r["employee_id"] for r in db.execute(
                "SELECT employee_id FROM job_assignments WHERE job_id=? ORDER BY employee_id ASC",
                (job_id,)
            ).fetchall()
        ]
        
        return jsonify({
            "ok": True,
            "job": job_dict,
            "materials": materials,
            "tools": tools,
            "assignments": assignments
        })
    except Exception as e:
        logger.error(f"Error fetching job detail: {e}")
        return jsonify({"ok": False, "error": "database_error"}), 500


@app.route("/api/jobs/<int:job_id>/materials", methods=["POST", "DELETE"])
def api_job_materials(job_id):
    """Správa materiálu pro zakázku"""
    u, err = require_role(write=True)
    if err:
        return err
    
    db = get_db()
    
    if request.method == "POST":
        data = request.get_json(force=True, silent=True) or {}
        
        name = (data.get("name") or "").strip()
        qty = data.get("qty", 0)
        unit = (data.get("unit") or "ks").strip()
        
        if not name:
            return jsonify({"ok": False, "error": "missing_name"}), 400
        
        try:
            qty = float(qty)
        except (ValueError, TypeError):
            return jsonify({"ok": False, "error": "invalid_quantity"}), 400
        
        try:
            db.execute(
                "INSERT INTO job_materials(job_id, name, qty, unit) VALUES (?, ?, ?, ?)",
                (job_id, name, qty, unit)
            )
            db.commit()
            logger.info(f"Material added to job {job_id}: {name}")
            return jsonify({"ok": True})
        except Exception as e:
            logger.error(f"Error adding material: {e}")
            db.rollback()
            return jsonify({"ok": False, "error": "database_error"}), 500
    
    if request.method == "DELETE":
        mid = request.args.get("id", type=int)
        
        if not mid:
            return jsonify({"ok": False, "error": "missing_id"}), 400
        
        try:
            db.execute(
                "DELETE FROM job_materials WHERE id=? AND job_id=?",
                (mid, job_id)
            )
            db.commit()
            logger.info(f"Material deleted: ID {mid} from job {job_id}")
            return jsonify({"ok": True})
        except Exception as e:
            logger.error(f"Error deleting material: {e}")
            db.rollback()
            return jsonify({"ok": False, "error": "database_error"}), 500


@app.route("/api/jobs/<int:job_id>/tools", methods=["POST", "DELETE"])
def api_job_tools(job_id):
    """Správa nářadí pro zakázku"""
    u, err = require_role(write=True)
    if err:
        return err
    
    db = get_db()
    
    if request.method == "POST":
        data = request.get_json(force=True, silent=True) or {}
        
        name = (data.get("name") or "").strip()
        qty = data.get("qty", 0)
        unit = (data.get("unit") or "ks").strip()
        
        if not name:
            return jsonify({"ok": False, "error": "missing_name"}), 400
        
        try:
            qty = float(qty)
        except (ValueError, TypeError):
            return jsonify({"ok": False, "error": "invalid_quantity"}), 400
        
        try:
            db.execute(
                "INSERT INTO job_tools(job_id, name, qty, unit) VALUES (?, ?, ?, ?)",
                (job_id, name, qty, unit)
            )
            db.commit()
            logger.info(f"Tool added to job {job_id}: {name}")
            return jsonify({"ok": True})
        except Exception as e:
            logger.error(f"Error adding tool: {e}")
            db.rollback()
            return jsonify({"ok": False, "error": "database_error"}), 500
    
    if request.method == "DELETE":
        tid = request.args.get("id", type=int)
        
        if not tid:
            return jsonify({"ok": False, "error": "missing_id"}), 400
        
        try:
            db.execute(
                "DELETE FROM job_tools WHERE id=? AND job_id=?",
                (tid, job_id)
            )
            db.commit()
            logger.info(f"Tool deleted: ID {tid} from job {job_id}")
            return jsonify({"ok": True})
        except Exception as e:
            logger.error(f"Error deleting tool: {e}")
            db.rollback()
            return jsonify({"ok": False, "error": "database_error"}), 500


@app.route("/api/jobs/<int:job_id>/assignments", methods=["POST"])
def api_job_assignments(job_id):
    """Přiřazení zaměstnanců k zakázce"""
    u, err = require_role(write=True)
    if err:
        return err
    
    db = get_db()
    data = request.get_json(force=True, silent=True) or {}
    ids = data.get("employee_ids") or []
    
    if not isinstance(ids, list):
        return jsonify({"ok": False, "error": "invalid_input"}), 400
    
    try:
        # Smaž stávající přiřazení
        db.execute("DELETE FROM job_assignments WHERE job_id=?", (job_id,))
        
        # Vlož nová přiřazení
        for eid in ids:
            try:
                db.execute(
                    "INSERT OR IGNORE INTO job_assignments(job_id, employee_id) VALUES (?, ?)",
                    (job_id, int(eid))
                )
            except (ValueError, TypeError):
                continue
        
        db.commit()
        logger.info(f"Job {job_id} assignments updated: {len(ids)} employees")
        return jsonify({"ok": True})
    except Exception as e:
        logger.error(f"Error updating assignments: {e}")
        db.rollback()
        return jsonify({"ok": False, "error": "database_error"}), 500


# ============================================================================
# API - ARCHIV ZAKÁZEK
# ============================================================================

@app.route("/api/jobs/archive")
def api_jobs_archive():
    """Archiv dokončených zakázek"""
    u, err = require_auth()
    if err:
        return err
    
    db = get_db()
    
    try:
        rows = db.execute("""
            SELECT id, title, client, city, code, status, date, completed_at
            FROM jobs
            WHERE LOWER(status) LIKE 'dokon%'
            ORDER BY COALESCE(date(completed_at), date(date)) DESC
        """).fetchall()
        
        months = {}
        for r in rows:
            r_dict = dict(r)
            src = r_dict.get("completed_at") or r_dict.get("date") or ""
            
            ym = ""
            try:
                if src and len(src) >= 7:
                    ym = f"{src[0:4]}-{src[5:7]}"
            except Exception:
                ym = ""
            
            key = ym or "unknown"
            if key not in months:
                months[key] = []
            months[key].append(r_dict)
        
        return jsonify({"ok": True, "months": months})
    except Exception as e:
        logger.error(f"Error fetching archive: {e}")
        return jsonify({"ok": False, "error": "database_error"}), 500


# ============================================================================
# MAIN
# ============================================================================

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    debug = os.environ.get("FLASK_ENV") != "production"
    
    if debug:
        logger.warning("Running in DEBUG mode - NOT FOR PRODUCTION!")
    
    app.run(host="0.0.0.0", port=port, debug=debug)
