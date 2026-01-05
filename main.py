import os, re, io, sqlite3, json
from datetime import datetime, date, timedelta
from flask import Flask, abort, g, jsonify, render_template, request, send_file, send_from_directory, session, redirect
import uuid
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
from assignment_helpers import (
    assign_employees_to_task, assign_employees_to_issue,
    get_task_assignees, get_issue_assignees,
    get_employee_tasks, get_employee_issues
)

# Database path configuration
# Priority: 1. DB_PATH env var, 2. Persistent disk detection, 3. Default
if os.environ.get("DB_PATH"):
    # User explicitly set DB_PATH - use it
    DB_PATH = os.environ.get("DB_PATH")
elif os.environ.get("RENDER") or os.environ.get("RENDER_EXTERNAL_HOSTNAME"):
    # Render platform detected - try persistent disk paths
    if os.path.exists("/var/data"):
        DB_PATH = "/var/data/app.db"
    elif os.path.exists("/persistent"):
        DB_PATH = "/persistent/app.db"
    elif os.path.exists("/data"):
        DB_PATH = "/data/app.db"
    else:
        # Fallback to /tmp which is persistent on Render
        DB_PATH = "/tmp/app.db"
else:
    # Local development
    DB_PATH = "app.db"

SECRET_KEY = os.environ.get("SECRET_KEY", "dev-" + os.urandom(16).hex())

# Upload directory configuration - use same logic as DB_PATH
if os.environ.get("UPLOAD_DIR"):
    UPLOAD_DIR = os.environ.get("UPLOAD_DIR")
elif os.environ.get("RENDER") or os.environ.get("RENDER_EXTERNAL_HOSTNAME"):
    if os.path.exists("/var/data"):
        UPLOAD_DIR = "/var/data/uploads"
    elif os.path.exists("/persistent"):
        UPLOAD_DIR = "/persistent/uploads"
    elif os.path.exists("/data"):
        UPLOAD_DIR = "/data/uploads"
    else:
        UPLOAD_DIR = "/tmp/uploads"
else:
    UPLOAD_DIR = "uploads"

app = Flask(__name__, static_folder=".", static_url_path="")
app.secret_key = SECRET_KEY

# ----------------- Role definitions -----------------
# Pozn.: role 'team_lead' byla v předchozích verzích; pro kompatibilitu ji mapujeme na 'lander'.
ROLES = ("owner", "admin", "manager", "lander", "worker")
WRITE_ROLES = ("owner", "admin", "manager", "lander")

def normalize_role(role):
    """Normalizace role pro zpětnou kompatibilitu a konzistentní autorizaci."""
    if not role:
        return "owner"
    role = str(role).strip().lower()
    if role == "team_lead":
        return "lander"
    return role
os.makedirs(UPLOAD_DIR, exist_ok=True)

# ----------------- Database utilities -----------------
def get_db():
    if "db" not in g:
        # Ensure directory exists for DB_PATH
        db_dir = os.path.dirname(DB_PATH)
        if db_dir and not os.path.exists(db_dir):
            try:
                os.makedirs(db_dir, exist_ok=True)
                print(f"[DB] Created directory: {db_dir}")
            except Exception as e:
                print(f"[DB] Warning: Could not create directory {db_dir}: {e}")
        
        # Log database path (only once at startup)
        if not hasattr(get_db, '_logged'):
            print(f"[DB] ==================== DATABASE DEBUG ====================")
            print(f"[DB] Using database: {DB_PATH}")
            print(f"[DB] Database file exists: {os.path.exists(DB_PATH)}")
            if os.path.exists(DB_PATH):
                print(f"[DB] Database file size: {os.path.getsize(DB_PATH)} bytes")
            print(f"[DB] RENDER env var: {os.environ.get('RENDER', 'NOT SET')}")
            print(f"[DB] /var/data exists: {os.path.exists('/var/data')}")
            if os.path.exists('/var/data'):
                print(f"[DB] /var/data contents: {os.listdir('/var/data')}")
            print(f"[DB] =========================================================")
            get_db._logged = True
        
        # Connect with WAL mode for better concurrency
        g.db = sqlite3.connect(DB_PATH, check_same_thread=False)
        g.db.row_factory = sqlite3.Row
        
        # Enable WAL mode for better performance and durability
        try:
            g.db.execute("PRAGMA journal_mode=WAL")
        except Exception:
            pass
        
        # Run migrations once per app instance
        if not hasattr(get_db, '_migrations_done'):
            print("[DB] Running migrations...")
            try:
                # Create missing tables
                g.db.executescript("""
                    CREATE TABLE IF NOT EXISTS issues (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        job_id INTEGER NOT NULL,
                        title TEXT NOT NULL,
                        description TEXT,
                        type TEXT NOT NULL DEFAULT 'blocker',
                        status TEXT NOT NULL DEFAULT 'open',
                        severity TEXT,
                        assigned_to INTEGER,
                        created_by INTEGER NOT NULL,
                        created_at TEXT NOT NULL DEFAULT (datetime('now')),
                        updated_at TEXT DEFAULT (datetime('now')),
                        resolved_at TEXT,
                        FOREIGN KEY (job_id) REFERENCES jobs(id) ON DELETE CASCADE,
                        FOREIGN KEY (assigned_to) REFERENCES employees(id) ON DELETE SET NULL,
                        FOREIGN KEY (created_by) REFERENCES users(id)
                    );
                    
                    CREATE INDEX IF NOT EXISTS idx_issues_job_id ON issues(job_id);
                    CREATE INDEX IF NOT EXISTS idx_issues_assigned_to ON issues(assigned_to);
                    CREATE INDEX IF NOT EXISTS idx_issues_status ON issues(status);
                    
                    CREATE TABLE IF NOT EXISTS issue_assignments (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        issue_id INTEGER NOT NULL,
                        employee_id INTEGER NOT NULL,
                        is_primary BOOLEAN DEFAULT 0,
                        created_at TEXT DEFAULT (datetime('now')),
                        FOREIGN KEY (issue_id) REFERENCES issues(id) ON DELETE CASCADE,
                        FOREIGN KEY (employee_id) REFERENCES employees(id) ON DELETE CASCADE,
                        UNIQUE(issue_id, employee_id)
                    );
                    
                    CREATE INDEX IF NOT EXISTS idx_issue_assignments_issue_id ON issue_assignments(issue_id);
                    CREATE INDEX IF NOT EXISTS idx_issue_assignments_employee_id ON issue_assignments(employee_id);
                    
                    CREATE TABLE IF NOT EXISTS task_assignments (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        task_id INTEGER NOT NULL,
                        employee_id INTEGER NOT NULL,
                        is_primary BOOLEAN DEFAULT 0,
                        created_at TEXT DEFAULT (datetime('now')),
                        FOREIGN KEY (task_id) REFERENCES tasks(id) ON DELETE CASCADE,
                        FOREIGN KEY (employee_id) REFERENCES employees(id) ON DELETE CASCADE,
                        UNIQUE(task_id, employee_id)
                    );
                    
                    CREATE INDEX IF NOT EXISTS idx_task_assignments_task_id ON task_assignments(task_id);
                    CREATE INDEX IF NOT EXISTS idx_task_assignments_employee_id ON task_assignments(employee_id);
                    
                    CREATE TABLE IF NOT EXISTS issue_attachments (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        issue_id INTEGER,
                        filename TEXT NOT NULL,
                        original_filename TEXT NOT NULL,
                        file_path TEXT NOT NULL,
                        file_size INTEGER,
                        mime_type TEXT,
                        uploaded_by INTEGER,
                        uploaded_at TEXT DEFAULT (datetime('now')),
                        FOREIGN KEY (issue_id) REFERENCES issues(id) ON DELETE CASCADE,
                        FOREIGN KEY (uploaded_by) REFERENCES employees(id)
                    );
                    
                    CREATE TABLE IF NOT EXISTS task_attachments (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        task_id INTEGER,
                        filename TEXT NOT NULL,
                        original_filename TEXT NOT NULL,
                        file_path TEXT NOT NULL,
                        file_size INTEGER,
                        mime_type TEXT,
                        uploaded_by INTEGER,
                        uploaded_at TEXT DEFAULT (datetime('now')),
                        FOREIGN KEY (task_id) REFERENCES tasks(id) ON DELETE CASCADE,
                        FOREIGN KEY (uploaded_by) REFERENCES employees(id)
                    );
                    
                    CREATE TABLE IF NOT EXISTS issue_comments (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        issue_id INTEGER NOT NULL,
                        user_id INTEGER,
                        comment TEXT NOT NULL,
                        created_at TEXT DEFAULT (datetime('now')),
                        FOREIGN KEY (issue_id) REFERENCES issues(id) ON DELETE CASCADE,
                        FOREIGN KEY (user_id) REFERENCES employees(id)
                    );
                    
                    CREATE TABLE IF NOT EXISTS task_comments (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        task_id INTEGER NOT NULL,
                        user_id INTEGER,
                        comment TEXT NOT NULL,
                        created_at TEXT DEFAULT (datetime('now')),
                        FOREIGN KEY (task_id) REFERENCES tasks(id) ON DELETE CASCADE,
                        FOREIGN KEY (user_id) REFERENCES employees(id)
                    );
                    
                    CREATE TABLE IF NOT EXISTS issue_locations (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        issue_id INTEGER,
                        latitude REAL NOT NULL,
                        longitude REAL NOT NULL,
                        address TEXT,
                        created_at TEXT DEFAULT (datetime('now')),
                        FOREIGN KEY (issue_id) REFERENCES issues(id) ON DELETE CASCADE
                    );
                    
                    CREATE TABLE IF NOT EXISTS task_locations (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        task_id INTEGER,
                        latitude REAL NOT NULL,
                        longitude REAL NOT NULL,
                        address TEXT,
                        created_at TEXT DEFAULT (datetime('now')),
                        FOREIGN KEY (task_id) REFERENCES tasks(id) ON DELETE CASCADE
                    );
                """)
                g.db.commit()
                print("[DB] ✓ Migrations completed")
            except Exception as e:
                print(f"[DB] ✗ Migration error: {e}")
                g.db.rollback()
            
            get_db._migrations_done = True
        
        # Debug: Count records in key tables
        if not hasattr(get_db, '_count_logged'):
            try:
                jobs_count = g.db.execute("SELECT COUNT(*) FROM jobs").fetchone()[0]
                print(f"[DB] Jobs count: {jobs_count}")
            except Exception as e:
                print(f"[DB] Error counting jobs: {e}")
            
            try:
                employees_count = g.db.execute("SELECT COUNT(*) FROM employees").fetchone()[0]
                print(f"[DB] Employees count: {employees_count}")
            except Exception as e:
                print(f"[DB] Error counting employees: {e}")
            
            get_db._count_logged = True
    return g.db

@app.teardown_appcontext
def close_db(error=None):
    db = g.pop("db", None)
    if db is not None:
        try:
            # Ensure all changes are committed before closing
            db.commit()
        except Exception:
            pass
        db.close()

# ----------------- Utility functions -----------------
def _normalize_date(v):
    if not v:
        return v
    s = str(v).strip()
    import re as _re
    m = _re.match(r"^(\d{4})-(\d{1,2})-(\d{1,2})$", s)
    if m:
        y, M, d = m.groups()
        return f"{int(y):04d}-{int(M):02d}-{int(d):02d}"
    m = _re.match(r"^(\d{1,2})[\.\s-](\d{1,2})[\.\s-](\d{4})$", s)
    if m:
        d, M, y = m.groups()
        return f"{int(y):04d}-{int(M):02d}-{int(d):02d}"
    return s





@app.route("/archive")
def view_archive():
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



@app.route("/api/jobs/archive")
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

# --- Team/Employees aliases (to avoid 404) ---
from flask import render_template

@app.route("/team")
@app.route("/team/")
@app.route("/employees")
@app.route("/employees/")
@app.route("/zamestnanci")
@app.route("/zamestnanci/")
def team_alias():
    # Try to render team.html, fallback to employees.html
    try:
        return render_template("team.html")
    except:
        try:
            return render_template("employees.html")
        except:
            return send_from_directory(".", "employees.html")

@app.route("/admin/roles")
@app.route("/admin/roles/")
@app.route("/admin_roles.html")
def admin_roles():
    """Stránka pro správu rolí - pouze pro ownera"""
    u, err = require_auth()
    if err:
        return redirect('/login')
    if u and u.get('role') not in ('owner', 'admin'):
        return jsonify({"ok": False, "error": "forbidden"}), 403
    return render_template("admin_roles.html")
# --- end aliases ---

# ----------------- Migration -----------------
def _migrate_completed_at():
    """Add missing columns to jobs table if they don't exist"""
    db = get_db()
    try:
        cols = [r[1] for r in db.execute("PRAGMA table_info(jobs)").fetchall()]
        if "completed_at" not in cols:
            db.execute("ALTER TABLE jobs ADD COLUMN completed_at TEXT")
            db.commit()
            print("[DB] Added column: completed_at")
        if "created_date" not in cols:
            db.execute("ALTER TABLE jobs ADD COLUMN created_date TEXT")
            db.commit()
            print("[DB] Added column: created_date")
        if "start_date" not in cols:
            db.execute("ALTER TABLE jobs ADD COLUMN start_date TEXT")
            db.commit()
            print("[DB] Added column: start_date")
        if "progress" not in cols:
            db.execute("ALTER TABLE jobs ADD COLUMN progress INTEGER DEFAULT 0")
            db.commit()
            print("[DB] Added column: progress")
    except Exception as e:
        print(f"[DB] Migration warning: {e}")

def _migrate_employees_enhanced():
    """Add enhanced columns to employees table and create new tables"""
    db = get_db()
    try:
        cols = [r[1] for r in db.execute("PRAGMA table_info(employees)").fetchall()]
        
        # Add new columns to employees table
        new_cols = {
            "birth_date": "TEXT",
            "contract_type": "TEXT DEFAULT 'HPP'",
            "start_date": "TEXT",
            "hourly_rate": "REAL",
            "salary": "REAL",
            "skills": "TEXT",
            "location": "TEXT",
            "status": "TEXT DEFAULT 'active'",
            "rating": "REAL DEFAULT 0",
            "avatar_url": "TEXT"
        
            ,"user_id": "INTEGER NULL"
        }
        
        for col_name, col_def in new_cols.items():
            if col_name not in cols:
                db.execute(f"ALTER TABLE employees ADD COLUMN {col_name} {col_def}")
                db.commit()
                print(f"[DB] Added column: employees.{col_name}")
        
        # Create employee_documents table
        db.execute("""
            CREATE TABLE IF NOT EXISTS employee_documents (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                employee_id INTEGER NOT NULL,
                type TEXT NOT NULL,
                file_url TEXT NOT NULL,
                uploaded_at TEXT NOT NULL DEFAULT (datetime('now')),
                FOREIGN KEY (employee_id) REFERENCES employees(id) ON DELETE CASCADE
            )
        """)
        db.commit()
        print("[DB] Created table: employee_documents")
        
        # Create employee_timeline table
        db.execute("""
            CREATE TABLE IF NOT EXISTS employee_timeline (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                employee_id INTEGER NOT NULL,
                action TEXT NOT NULL,
                description TEXT,
                created_at TEXT NOT NULL DEFAULT (datetime('now')),
                FOREIGN KEY (employee_id) REFERENCES employees(id) ON DELETE CASCADE
            )
        """)
        db.commit()
        print("[DB] Created table: employee_timeline")
        
    except Exception as e:
        print(f"[DB] Migration warning: {e}")

def _migrate_roles_and_hierarchy():
    """Migrace: přidání sloupců role a manager_id do users tabulky"""
    db = get_db()
    try:
        # Zkontrolovat existující sloupce
        cols = [r[1] for r in db.execute("PRAGMA table_info(users)").fetchall()]
        
        # Přidat sloupec role pokud neexistuje nebo aktualizovat CHECK constraint
        if 'role' not in cols:
            db.execute("ALTER TABLE users ADD COLUMN role VARCHAR(20) DEFAULT 'worker'")
            db.commit()
            print("[DB] Added column: users.role")
        else:
            # Aktualizovat CHECK constraint pro nové role
            # SQLite nepodporuje ALTER COLUMN, takže musíme vytvořit novou tabulku
            # Poznámka: Pokud už existuje manager_id, přeskočíme tuto část
            if 'manager_id' not in cols:
                try:
                    # Vypnout foreign key kontroly během migrace
                    db.execute("PRAGMA foreign_keys=OFF")
                    db.execute("""
                        CREATE TABLE users_new (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            email TEXT UNIQUE NOT NULL,
                            name TEXT NOT NULL,
                            role TEXT NOT NULL DEFAULT 'worker' CHECK(role IN ('owner','admin','manager','lander','worker','team_lead')),
                            password_hash TEXT NOT NULL,
                            active INTEGER NOT NULL DEFAULT 1,
                            created_at TEXT NOT NULL DEFAULT (datetime('now')),
                            manager_id INTEGER NULL
                        )
                    """)
                    db.execute("""
                        INSERT INTO users_new (id, email, name, role, password_hash, active, created_at)
                        SELECT id, email, name, 
                               CASE 
                                   WHEN role = 'admin' THEN 'owner'
                                   ELSE role
                               END,
                               password_hash, active, created_at
                        FROM users
                    """)
                    db.execute("DROP TABLE users")
                    db.execute("ALTER TABLE users_new RENAME TO users")
                    db.execute("PRAGMA foreign_keys=ON")
                    db.commit()
                    print("[DB] Updated users table with new role system")
                except Exception as e:
                    db.execute("PRAGMA foreign_keys=ON")
                    print(f"[DB] Role migration warning: {e}")
        
        # Přidat manager_id pokud neexistuje
        if 'manager_id' not in cols:
            db.execute("ALTER TABLE users ADD COLUMN manager_id INTEGER NULL")
            db.commit()
            print("[DB] Added column: users.manager_id")
            
            # Přidat foreign key constraint (SQLite to podporuje přes CREATE INDEX)
            try:
                db.execute("CREATE INDEX IF NOT EXISTS idx_users_manager_id ON users(manager_id)")
                db.commit()
            except Exception as e:
                print(f"[DB] Index creation warning: {e}")
        
        # Aktualizovat existujícího uživatele david@greendavid.cz na owner
        try:
            db.execute("UPDATE users SET role = 'owner' WHERE email = 'david@greendavid.cz'")
            db.commit()
            print("[DB] Updated david@greendavid.cz to owner role")
        except Exception as e:
            print(f"[DB] Owner update warning: {e}")
            
    except Exception as e:
        print(f"[DB] Roles migration warning: {e}")

# Run migration after all functions are defined
try:
    with app.app_context():
        _migrate_completed_at()
        _migrate_employees_enhanced()
        _migrate_roles_and_hierarchy()
except Exception as e:
    print(f"[DB] Migration failed: {e}")

# ----------------- Authentication functions -----------------
def current_user():
    uid = session.get("uid")
    if not uid:
        return None
    db = get_db()
    # Zkontrolovat, zda existuje sloupec manager_id
    cols = [r[1] for r in db.execute("PRAGMA table_info(users)").fetchall()]
    if 'manager_id' in cols:
        row = db.execute("SELECT id,email,name,role,active,manager_id FROM users WHERE id=?", (uid,)).fetchone()
    else:
        row = db.execute("SELECT id,email,name,role,active FROM users WHERE id=?", (uid,)).fetchone()
    return dict(row) if row else None

def require_auth():
    u = current_user()
    if not u or not u.get("active"):
        return None, (jsonify({"ok": False, "error": "unauthorized"}), 401)
    return u, None

def require_role(write=False):
    u, err = require_auth()
    if err:
        return None, err
    if write and normalize_role(u["role"]) not in WRITE_ROLES:
        return None, (jsonify({"ok": False, "error": "forbidden"}), 403)
    return u, None

# ----------------- Permissions system -----------------
from functools import wraps

def requires_role(*allowed_roles):
    """Decorator pro kontrolu oprávnění podle role"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Kontrola přihlášení
            if 'uid' not in session:
                return jsonify({'ok': False, 'error': 'unauthorized'}), 401
            
            # Získat roli uživatele z DB
            db = get_db()
            user = db.execute(
                "SELECT role FROM users WHERE id = ?", 
                (session['uid'],)
            ).fetchone()
            
            if not user:
                return jsonify({'ok': False, 'error': 'unauthorized'}), 401
            
            # Fallback: pokud nemá roli nebo je NULL, považujeme za owner (pro zpětnou kompatibilitu)
            user_role = user['role'] or 'owner'
            
            if user_role not in allowed_roles:
                return jsonify({'ok': False, 'error': 'forbidden'}), 403
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def get_current_user():
    """Pomocná funkce pro získání aktuálního uživatele s plnými informacemi"""
    if 'uid' not in session:
        return None
    
    db = get_db()
    user = db.execute(
        "SELECT id, email, name, role, manager_id FROM users WHERE id = ?",
        (session['uid'],)
    ).fetchone()
    
    if not user:
        return None
    
    user_dict = dict(user)
    
    # Fallback: pokud nemá roli nebo je NULL, považujeme za owner (pro zpětnou kompatibilitu)
    if not user_dict.get('role') or user_dict['role'] == 'admin':
        user_dict['role'] = 'owner'
    
    return user_dict

def can_manage_employee(manager_id, employee_id):
    """Kontrola, zda má manager oprávnění spravovat zaměstnance"""
    db = get_db()
    
    # Owner může všechno
    manager = db.execute("SELECT role FROM users WHERE id = ?", (manager_id,)).fetchone()
    if manager and manager['role'] in ('owner', 'admin'):
        return True
    
    # Manager/Team lead jen své lidi
    employee = db.execute(
        "SELECT manager_id FROM users WHERE id = ?", 
        (employee_id,)
    ).fetchone()
    
    return employee and employee['manager_id'] == manager_id

# ----------------- bootstrap (subset) -----------------
def ensure_schema():
    db = get_db()
    db.executescript("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        email TEXT UNIQUE NOT NULL,
        name TEXT NOT NULL,
        role TEXT NOT NULL DEFAULT 'worker' CHECK(role IN ('owner','manager','team_lead','worker','admin')),
        password_hash TEXT NOT NULL,
        active INTEGER NOT NULL DEFAULT 1,
        created_at TEXT NOT NULL DEFAULT (datetime('now')),
        manager_id INTEGER NULL
    );
    CREATE TABLE IF NOT EXISTS employees (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        role TEXT NOT NULL DEFAULT 'worker',
        phone TEXT DEFAULT '',
        email TEXT DEFAULT '',
        address TEXT DEFAULT '',
        user_id INTEGER NULL
    );
    -- prefer new schema; legacy DBs may still have jobs.name (possibly NOT NULL)
    CREATE TABLE IF NOT EXISTS jobs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT,
        name TEXT,
        client TEXT NOT NULL DEFAULT '',
        status TEXT NOT NULL DEFAULT 'Plán',
        city TEXT NOT NULL DEFAULT '',
        code TEXT NOT NULL DEFAULT '',
        date TEXT,
        note TEXT
    );
    
    CREATE TABLE IF NOT EXISTS job_assignments (
        job_id INTEGER NOT NULL,
        employee_id INTEGER NOT NULL,
        PRIMARY KEY (job_id, employee_id)
    );
    CREATE TABLE IF NOT EXISTS job_materials (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        job_id INTEGER NOT NULL,
        name TEXT NOT NULL,
        qty REAL NOT NULL DEFAULT 0,
        unit TEXT NOT NULL DEFAULT 'ks'
    );
    CREATE TABLE IF NOT EXISTS job_tools (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        job_id INTEGER NOT NULL,
        name TEXT NOT NULL,
        qty REAL NOT NULL DEFAULT 0,
        unit TEXT NOT NULL DEFAULT 'ks'
    );
    CREATE TABLE IF NOT EXISTS tasks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        job_id INTEGER,
        employee_id INTEGER,
        title TEXT NOT NULL,
        description TEXT DEFAULT '',
        status TEXT NOT NULL DEFAULT 'open',
        due_date TEXT
    );
    CREATE TABLE IF NOT EXISTS timesheets (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        employee_id INTEGER NOT NULL,
        job_id INTEGER NOT NULL,
        date TEXT NOT NULL,
        hours REAL NOT NULL DEFAULT 0,
        place TEXT DEFAULT '',
        activity TEXT DEFAULT ''
    );
    CREATE TABLE IF NOT EXISTS calendar_events (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        date TEXT NOT NULL,
        title TEXT NOT NULL,
        kind TEXT NOT NULL DEFAULT 'note',
        job_id INTEGER,
        start_time TEXT,
        end_time TEXT,
        note TEXT DEFAULT '',
        color TEXT DEFAULT '#2e7d32'
    );
    """)
    # Migrace: přidání sloupců phone, email, address do employees (pokud neexistují)
    try:
        db.execute("ALTER TABLE employees ADD COLUMN phone TEXT DEFAULT ''")
    except Exception:
        pass  # Sloupec už existuje
    try:
        db.execute("ALTER TABLE employees ADD COLUMN email TEXT DEFAULT ''")
    except Exception:
        pass  # Sloupec už existuje
    try:
        db.execute("ALTER TABLE employees ADD COLUMN address TEXT DEFAULT ''")
    except Exception:
        pass  # Sloupec už existuje
    db.commit()

def seed_admin():
    db = get_db()
    cur = db.execute("SELECT COUNT(*) c FROM users")
    if cur.fetchone()["c"] == 0:
        db.execute(
            "INSERT INTO users(email,name,role,password_hash,active,created_at) VALUES (?,?,?,?,1,?)",
            (
                os.environ.get("ADMIN_EMAIL","admin@greendavid.local"),
                os.environ.get("ADMIN_NAME","Admin"),
                "owner",  # Vytvořit jako owner místo admin
                generate_password_hash(os.environ.get("ADMIN_PASSWORD","admin123"), method='pbkdf2:sha256'),
                datetime.utcnow().isoformat()
            )
        )
        db.commit()

def _auto_upgrade_admins_to_owner():
    """Automaticky upgrade admin účtů na owner při startu"""
    db = get_db()
    try:
        # Upgrade známých admin emailů
        admin_emails = ['admin@greendavid.local', 'david@greendavid.cz', 'admin@greendavid.cz', 'admin@example.com']
        for email in admin_emails:
            result = db.execute(
                "UPDATE users SET role = 'owner' WHERE email = ? AND (role IS NULL OR role != 'owner' OR role = 'admin')",
                (email,)
            )
            if result.rowcount > 0:
                db.commit()
                print(f"[DB] Auto-upgraded {email} to owner role")
        
        # Pokud žádný owner neexistuje, upgrade prvního uživatele
        owner_exists = db.execute("SELECT COUNT(*) as cnt FROM users WHERE role = 'owner'").fetchone()
        if owner_exists['cnt'] == 0:
            first_user = db.execute("SELECT id, email FROM users ORDER BY id LIMIT 1").fetchone()
            if first_user:
                db.execute("UPDATE users SET role = 'owner' WHERE id = ?", (first_user['id'],))
                db.commit()
                print(f"[DB] Auto-upgraded first user {first_user['email']} to owner role")
        
        # Upgrade všech admin účtů na owner
        result = db.execute(
            "UPDATE users SET role = 'owner' WHERE role = 'admin' OR role IS NULL"
        )
        if result.rowcount > 0:
            db.commit()
            print(f"[DB] Auto-upgraded {result.rowcount} admin/NULL accounts to owner role")
    except Exception as e:
        print(f"[DB] Warning: Could not auto-upgrade admin: {e}")

def seed_employees():
    db = get_db()
    cur = db.execute("SELECT COUNT(*) c FROM employees")
    if cur.fetchone()["c"] == 0:
        # Původní zaměstnanci
        employees = [
            ("david", "zahradník"),
            ("vendi", "zahradník"),
            ("jason", "zahradník"),
        ]
        for name, role in employees:
            db.execute("INSERT INTO employees(name,role) VALUES (?,?)", (name, role))
        db.commit()

@app.before_request
def _ensure():
    ensure_schema()
    seed_admin()
    _auto_upgrade_admins_to_owner()
    seed_employees()

# ----------------- helpers for jobs schema compat -----------------
def _jobs_info():
    rows = get_db().execute("PRAGMA table_info(jobs)").fetchall()
    # rows: cid, name, type, notnull, dflt_value, pk
    return {r[1]: {"notnull": int(r[3])} for r in rows}

def _job_title_col():
    info = _jobs_info()
    if "title" in info:
        return "title"
    return "name" if "name" in info else "title"

def _job_select_all():
    info = _jobs_info()
    base_cols = "id, client, status, city, code, date, note"
    date_cols = ", created_date, start_date" if "created_date" in _jobs_info() else ""
    progress_col = ", progress" if "progress" in _jobs_info() else ""
    if "title" in info:
        return f"SELECT title, {base_cols}{date_cols}{progress_col} FROM jobs"
    if "name" in info:
        return f"SELECT name AS title, {base_cols}{date_cols}{progress_col} FROM jobs"
    return f"SELECT '' AS title, {base_cols}{date_cols}{progress_col} FROM jobs"

def _job_insert_cols_and_vals(title, client, status, city, code, dt, note, owner_id=None):
    info = _jobs_info()
    cols = []
    vals = []
    # Keep legacy 'name' in sync if present
    if "title" in info:
        cols.append("title"); vals.append(title)
    if "name" in info:
        cols.append("name"); vals.append(title)
    cols += ["client","status","city","code","date","note"]
    vals += [client, status, city, code, dt, note]
    # legacy NOT NULL columns without defaults
    now = datetime.utcnow().isoformat()
    if "created_at" in info:
        cols.append("created_at"); vals.append(now)
    if "updated_at" in info:
        cols.append("updated_at"); vals.append(now)
    # legacy owner_id
    if "owner_id" in info:
        if owner_id is None:
            cu = current_user()
            owner_id = cu["id"] if cu else None
        cols.append("owner_id"); vals.append(int(owner_id) if owner_id is not None else None)
    return cols, vals

def _job_title_update_set(params_list, title_value):
    info = _jobs_info()
    sets = []
    if "title" in info:
        sets.append("title=?"); params_list.append(title_value)
    if "name" in info:
        sets.append("name=?"); params_list.append(title_value)
    return sets

# ----------------- static -----------------
@app.route("/")
def index():
    return send_from_directory(".", "index.html")

@app.route("/static/<path:filename>")
def static_files(filename):
    """Serve static files from static/ directory"""
    return send_from_directory("static", filename)

@app.route("/uploads/<path:name>")
def uploaded_file(name):
    safe = re.sub(r"[^a-zA-Z0-9._-]", "_", name)
    path = os.path.join(UPLOAD_DIR, safe)
    if not os.path.isfile(path):
        abort(404)
    return send_from_directory(UPLOAD_DIR, safe)

@app.route("/health")
def health():
    return {"status": "ok"}

# ----------------- APIs -----------------
@app.route("/api/me")
def api_me():
    u = current_user()
    return jsonify({"ok": True, "authenticated": bool(u), "user": u, "tasks_count": 0})

# auth
@app.route("/api/login", methods=["POST"])
def api_login():
    data = request.get_json(force=True, silent=True) or {}
    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""
    db = get_db()
    row = db.execute("SELECT id,email,name,role,password_hash,active FROM users WHERE email=?", (email,)).fetchone()
    
    if not row or not row["active"]:
        return jsonify({"ok": False, "error": "invalid_credentials"}), 401
    
    # Safe password verification - handle scrypt incompatibility on Python 3.9
    try:
        password_valid = check_password_hash(row["password_hash"], password)
    except (AttributeError, ValueError) as e:
        # Scrypt not available in Python 3.9 - regenerate hash with pbkdf2
        print(f"[AUTH] Password hash error for {email}: {e}")
        # For security, reject and force password reset
        return jsonify({"ok": False, "error": "password_hash_incompatible"}), 401
    
    if not password_valid:
        return jsonify({"ok": False, "error": "invalid_credentials"}), 401
    
    # Normalizovat roli (admin -> owner, NULL -> owner)
    user_role = row["role"] or "owner"
    if user_role == "admin":
        user_role = "owner"
    
    # Auto-upgrade admin účtů na owner při přihlášení
    if row["role"] in (None, "admin"):
        db.execute("UPDATE users SET role = 'owner' WHERE id = ?", (row["id"],))
        db.commit()
        user_role = "owner"
        print(f"[DB] Auto-upgraded {email} to owner role on login")
    
    # store user id and role in session
    session["uid"] = row["id"]
    session["user_name"] = row["name"]
    session["user_email"] = row["email"]
    session["user_role"] = user_role
    return jsonify({"ok": True})

@app.route("/api/logout", methods=["POST"])
def api_logout():
    # remove user id from session
    session.pop("uid", None)
    return jsonify({"ok": True})

# employees
@app.route("/api/employees", methods=["GET","POST","PATCH","DELETE"])
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

            # Účet zaměstnance (pokud je navázaný přes employees.user_id)
            emp["has_account"] = emp.get("account_user_id") is not None
            if emp.get("account_role") is not None:
                emp["account_role"] = normalize_role(emp.get("account_role"))
            
            # Vypočítej hodiny tento týden
            from datetime import datetime, timedelta
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
            role = data.get("role") or "worker"
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
            
            # Build INSERT query with all available columns
            cols = [r[1] for r in db.execute("PRAGMA table_info(employees)").fetchall()]
            insert_cols = ["name", "role"]
            insert_vals = [name, role]
            
            for col in ["phone", "email", "address", "birth_date", "contract_type", "start_date", 
                       "hourly_rate", "salary", "skills", "location", "status", "rating", "avatar_url"]:
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
                      "start_date", "hourly_rate", "salary", "skills", "location", "status", "rating", "avatar_url"]
            for k in allowed:
                if k in data and k in cols:
                    updates.append(f"{k}=?")
                    # Handle numeric fields
                    if k in ["hourly_rate", "salary", "rating"]:
                        params.append(float(data[k]) if data[k] is not None else None)
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
@app.route("/api/users", methods=["GET"])
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

@app.route("/api/users", methods=["POST"])
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

@app.route("/api/users/<int:user_id>/role", methods=["PUT"])
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

# ----------------- Timesheets approval -----------------
@app.route("/api/timesheets/<int:timesheet_id>/approve", methods=["POST"])
@requires_role('owner', 'admin', 'manager', 'lander')
def api_approve_timesheet(timesheet_id):
    """Schválení výkazu - jen pro nadřízené"""
    user = get_current_user()
    if not user:
        return jsonify({"ok": False, "error": "unauthorized"}), 401
    
    db = get_db()
    
    # Získat timesheet
    timesheet = db.execute(
        "SELECT employee_id FROM timesheets WHERE id = ?",
        (timesheet_id,)
    ).fetchone()
    
    if not timesheet:
        return jsonify({"ok": False, "error": "not_found"}), 404
    
    # Kontrola oprávnění - owner může všechno
    if user['role'] not in ('owner', 'admin'):
        # Pro ostatní role potřebujeme zkontrolovat hierarchii
        # Pokud timesheets nemá přímý link na users, použijeme employees
        # Prozatím povolíme všem nadřízeným
        pass
    
    # Zkontrolovat, zda timesheets tabulka má sloupce pro schválení
    cols = [r[1] for r in db.execute("PRAGMA table_info(timesheets)").fetchall()]
    
    if 'approved' not in cols:
        db.execute("ALTER TABLE timesheets ADD COLUMN approved INTEGER DEFAULT 0")
        db.execute("ALTER TABLE timesheets ADD COLUMN approved_by INTEGER NULL")
        db.execute("ALTER TABLE timesheets ADD COLUMN approved_at TEXT NULL")
        db.commit()
    
    # Schválit
    try:
        db.execute(
            "UPDATE timesheets SET approved = 1, approved_by = ?, approved_at = datetime('now') WHERE id = ?",
            (user['id'], timesheet_id)
        )
        db.commit()
        return jsonify({"ok": True})
    except Exception as e:
        db.rollback()
        return jsonify({"ok": False, "error": str(e)}), 500

# ✅ jobs with legacy schema compatibility
@app.route("/api/jobs", methods=["GET","POST","PATCH","DELETE"])
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
            db.execute(sql, vals)
            db.commit()
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
            for f in ("client","status","city","code","date","note","created_date","start_date","progress"):
                if f in data:
                    if f=="date" or f=="created_date" or f=="start_date":
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
        db.execute("DELETE FROM jobs WHERE id=?", (jid,))
        db.commit()
        print(f"✓ Job {jid} deleted successfully")
        return jsonify({"ok": True})
    except Exception as e:
        db.rollback()
        print(f"✗ Error deleting job: {e}")
        return jsonify({"ok": False, "error": str(e)}), 500


# -------- Job detail & materials/tools/assignments --------
@app.route("/api/jobs/<int:job_id>", methods=["GET"])
def api_job_detail(job_id):
    u, err = require_role(write=False)
    if err: return err
    db = get_db()
    title_col = _job_title_col()
    job = db.execute(f"SELECT id, {title_col} AS title, client, status, city, code, date, note FROM jobs WHERE id=?", (job_id,)).fetchone()
    if not job: return jsonify({"ok": False, "error": "not_found"}), 404
    job = dict(job)
    if job.get("date"): job["date"] = _normalize_date(job["date"])
    mats = [dict(r) for r in db.execute("SELECT id, name, qty, unit FROM job_materials WHERE job_id=? ORDER BY id ASC", (job_id,)).fetchall()]
    tools = [dict(r) for r in db.execute("SELECT id, name, qty, unit FROM job_tools WHERE job_id=? ORDER BY id ASC", (job_id,)).fetchall()]
    assigns = [r["employee_id"] for r in db.execute("SELECT employee_id FROM job_assignments WHERE job_id=? ORDER BY employee_id ASC", (job_id,)).fetchall()]
    return jsonify({"ok": True, "job": job, "materials": mats, "tools": tools, "assignments": assigns})

@app.route("/api/jobs/<int:job_id>/materials", methods=["POST","DELETE"])
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

@app.route("/api/jobs/<int:job_id>/tools", methods=["POST","DELETE"])
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

@app.route("/api/jobs/<int:job_id>/assignments", methods=["POST"])
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
@app.route("/api/tasks", methods=["GET","POST","PATCH","PUT","DELETE"])
def api_tasks():
    u, err = require_role(write=(request.method!="GET"))
    if err: return err
    db = get_db()

    if request.method == "GET":
        task_id = request.args.get("id", type=int)
        if task_id:
            # Return single task by ID
            row = db.execute("""SELECT t.id, t.job_id, t.employee_id, t.title, t.description, t.status, t.due_date,
                                      e.name AS employee_name
                               FROM tasks t
                               LEFT JOIN employees e ON e.id=t.employee_id
                               WHERE t.id=?""", (task_id,)).fetchone()
            if not row:
                return jsonify({"ok": False, "error": "not_found"}), 404
            
            task = dict(row)
            task["assignees"] = get_task_assignees(db, task_id)
            return jsonify({"ok": True, "task": task})
        
        jid = request.args.get("job_id", type=int)
        employee_id = request.args.get("employee_id", type=int)
        
        q = """SELECT t.id, t.job_id, t.employee_id, t.title, t.description, t.status, t.due_date,
                      e.name AS employee_name
               FROM tasks t
               LEFT JOIN employees e ON e.id=t.employee_id"""
        conds=[]; params=[]
        if jid: conds.append("t.job_id=?"); params.append(jid)
        if employee_id:
            # Pokud je zadán employee_id, hledej přes assignments
            q = """SELECT DISTINCT t.id, t.job_id, t.employee_id, t.title, t.description, t.status, t.due_date,
                          e.name AS employee_name
                   FROM tasks t
                   LEFT JOIN employees e ON e.id=t.employee_id
                   LEFT JOIN task_assignments ta ON ta.task_id = t.id"""
            conds.append("(t.employee_id=? OR ta.employee_id=?)")
            params.extend([employee_id, employee_id])
        if conds: q += " WHERE " + " AND ".join(conds)
        q += " ORDER BY COALESCE(t.due_date,''), t.id ASC"
        rows = [dict(r) for r in db.execute(q, params).fetchall()]
        
        # Přidej assignees ke každému tasku
        for task in rows:
            task["assignees"] = get_task_assignees(db, task["id"])
        
        return jsonify({"ok": True, "tasks": rows})

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
                assign_employees_to_task(db, task_id, assigned_ids, primary_id)
                db.commit()
            
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
            
            # Update assignments if provided
            if "assigned_employees" in data:
                # Clear existing assignments
                db.execute("DELETE FROM task_assignments WHERE task_id=?", (tid,))
                
                # Add new assignments
                assigned_ids = data.get("assigned_employees", [])
                primary_id = data.get("primary_employee")
                if assigned_ids:
                    assign_employees_to_task(db, tid, assigned_ids, primary_id)
            
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
        db.execute("DELETE FROM tasks WHERE id=?", (tid,))
        db.commit()
        print(f"✓ Task {tid} deleted successfully")
        return jsonify({"ok": True})
    except Exception as e:
        db.rollback()
        print(f"✗ Error deleting task: {e}")
        return jsonify({"ok": False, "error": str(e)}), 500

# issues CRUD
@app.route("/api/issues", methods=["GET","POST","PATCH","DELETE"])
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
                assign_employees_to_issue(db, new_id, assigned_ids, primary_id)
                db.commit()
            
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
                    assign_employees_to_issue(db, issue_id, assigned_ids, primary_id)
            
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
            
            db.execute("DELETE FROM issues WHERE id = ?", (issue_id,))
            db.commit()
            print(f"✓ Issue {issue_id} deleted")
            return jsonify({"ok": True})
        except Exception as e:
            db.rollback()
            print(f"✗ Error deleting issue: {e}")
            return jsonify({"ok": False, "error": str(e)}), 500

# timesheets CRUD + export
@app.route("/api/timesheets", methods=["GET","POST","PATCH","DELETE"])
def api_timesheets():
    u, err = require_role(write=(request.method!="GET"))
    if err: return err
    db = get_db()

    if request.method == "GET":
        emp = request.args.get("employee_id", type=int)
        jid = request.args.get("job_id", type=int)
        d_from = _normalize_date(request.args.get("from"))
        d_to   = _normalize_date(request.args.get("to"))
        title_col = _job_title_col()
        q = f"""SELECT t.id,t.employee_id,t.job_id,t.date,t.hours,t.place,t.activity,
                      e.name AS employee_name, j.{title_col} AS job_title, j.code AS job_code
               FROM timesheets t
               LEFT JOIN employees e ON e.id=t.employee_id
               LEFT JOIN jobs j ON j.id=t.job_id"""
        conds=[]; params=[]
        if emp: conds.append("t.employee_id=?"); params.append(emp)
        if jid: conds.append("t.job_id=?"); params.append(jid)
        if d_from and d_to:
            conds.append("date(t.date) BETWEEN date(?) AND date(?)"); params.extend([d_from, d_to])
        elif d_from:
            conds.append("date(t.date) >= date(?)"); params.append(d_from)
        elif d_to:
            conds.append("date(t.date) <= date(?)"); params.append(d_to)
        if conds: q += " WHERE " + " AND ".join(conds)
        q += " ORDER BY t.date ASC, t.id ASC"
        rows = db.execute(q, params).fetchall()
        return jsonify({"ok": True, "rows":[dict(r) for r in rows]})

    if request.method == "POST":
        try:
            data = request.get_json(force=True, silent=True) or {}
            emp = data.get("employee_id"); job = data.get("job_id"); dt=data.get("date"); hours = data.get("hours")
            place = data.get("place") or ""; activity = data.get("activity") or ""
            if not all([emp,job,dt,(hours is not None)]): return jsonify({"ok": False, "error":"invalid_input"}), 400
            db.execute("INSERT INTO timesheets(employee_id,job_id,date,hours,place,activity) VALUES (?,?,?,?,?,?)",
                       (int(emp), int(job), _normalize_date(dt), float(hours), place, activity))
            db.commit()
            print(f"✓ Timesheet created successfully (emp:{emp}, job:{job}, date:{dt})")
            return jsonify({"ok": True})
        except Exception as e:
            db.rollback()
            print(f"✗ Error creating timesheet: {e}")
            return jsonify({"ok": False, "error": str(e)}), 500

    if request.method == "PATCH":
        try:
            data = request.get_json(force=True, silent=True) or {}
            tid = data.get("id")
            if not tid: return jsonify({"ok": False, "error":"missing_id"}), 400
            allowed = ["employee_id","job_id","date","hours","place","activity"]
            sets, vals = [], []
            for k in allowed:
                if k in data:
                    v = _normalize_date(data[k]) if k=="date" else data[k]
                    if k in ("employee_id","job_id"):
                        v = int(v)
                    if k == "hours":
                        v = float(v)
                    sets.append(f"{k}=?"); vals.append(v)
            if not sets:
                return jsonify({"ok": False, "error":"no_fields"}), 400
            vals.append(int(tid))
            db.execute("UPDATE timesheets SET "+",".join(sets)+" WHERE id=?", vals)
            db.commit()
            print(f"✓ Timesheet {tid} updated successfully")
            return jsonify({"ok": True})
        except Exception as e:
            db.rollback()
            print(f"✗ Error updating timesheet: {e}")
            return jsonify({"ok": False, "error": str(e)}), 500

    # DELETE
    try:
        tid = request.args.get("id", type=int)
        if not tid: return jsonify({"ok": False, "error":"missing_id"}), 400
        db.execute("DELETE FROM timesheets WHERE id=?", (tid,))
        db.commit()
        print(f"✓ Timesheet {tid} deleted successfully")
        return jsonify({"ok": True})
    except Exception as e:
        db.rollback()
        print(f"✗ Error deleting timesheet: {e}")
        return jsonify({"ok": False, "error": str(e)}), 500

@app.route("/api/timesheets/export")
def api_timesheets_export():
    u, err = require_role(write=False)
    if err: return err
    db = get_db()
    emp = request.args.get("employee_id", type=int)
    jid = request.args.get("job_id", type=int)
    d_from = _normalize_date(request.args.get("from"))
    d_to   = _normalize_date(request.args.get("to"))
    title_col = _job_title_col()
    q = f"""SELECT t.id,t.date,t.hours,t.place,t.activity,
                  e.name AS employee_name, e.id AS employee_id,
                  j.{title_col} AS job_title, j.code AS job_code, j.id AS job_id
           FROM timesheets t
           LEFT JOIN employees e ON e.id=t.employee_id
           LEFT JOIN jobs j ON j.id=t.job_id"""
    conds=[]; params=[]
    if emp: conds.append("t.employee_id=?"); params.append(emp)
    if jid: conds.append("t.job_id=?"); params.append(jid)
    if d_from and d_to:
        conds.append("date(t.date) BETWEEN date(?) AND date(?)"); params.extend([d_from, d_to])
    elif d_from:
        conds.append("date(t.date) >= date(?)"); params.append(d_from)
    elif d_to:
        conds.append("date(t.date) <= date(?)"); params.append(d_to)
    if conds: q += " WHERE " + " AND ".join(conds)
    q += " ORDER BY t.date ASC, t.id ASC"
    rows = get_db().execute(q, params).fetchall()

    output = io.StringIO()
    import csv as _csv
    writer = _csv.writer(output)
    writer.writerow(["id","date","employee_id","employee_name","job_id","job_title","job_code","hours","place","activity"])
    for r in rows:
        writer.writerow([r["id"], r["date"], r["employee_id"], r["employee_name"] or "", r["job_id"], r["job_title"] or "", r["job_code"] or "", r["hours"], r["place"] or "", r["activity"] or ""])
    mem = io.BytesIO(output.getvalue().encode("utf-8-sig"))
    mem.seek(0)
    fname = "timesheets.csv"
    return send_file(mem, mimetype="text/csv", as_attachment=True, download_name=fname)

# ----------------- Template route -----------------
@app.route("/timesheets.html")
def page_timesheets():
    # Render template version (keeps original Timesheets design) while using unified JS header via templates/layout.html
    return render_template("timesheets.html")
# ----------------- Standalone HTML routes -----------------
@app.route("/jobs.html")
def page_jobs():
    return send_from_directory(".", "jobs.html")

@app.route("/tasks.html")
def page_tasks():
    return send_from_directory(".", "tasks.html")

@app.route("/issues")
@app.route("/issues.html")
def page_issues():
    return send_from_directory(".", "issues.html")

@app.route("/employees.html")
def page_employees():
    return send_from_directory(".", "employees.html")

@app.route("/calendar.html")
def page_calendar():
    return send_from_directory(".", "calendar.html")

@app.route("/settings.html")
def page_settings():
    return send_from_directory(".", "settings.html")

@app.route("/warehouse.html")
def page_warehouse():
    return send_from_directory(".", "warehouse.html")

@app.route("/finance.html")
def page_finance():
    return send_from_directory(".", "finance.html")

@app.route("/documents.html")
def page_documents():
    return send_from_directory(".", "documents.html")

@app.route("/reports.html")
def page_reports():
    return send_from_directory(".", "reports.html")

# ----------------- Job detail UI routes -----------------
@app.route("/jobs/<int:job_id>")
def page_job_detail(job_id):
    # Classic server-rendered detail page with timesheet table
    return render_template("job_detail.html", job_id=job_id)

@app.route("/job.html")
def page_job_detail_query():
    jid = request.args.get("id", type=int)
    if not jid:
        # fallback to jobs tab if missing id
        return render_template("jobs_list.html")
    return render_template("job_detail.html", job_id=jid)

# ----------------- admin export / download -----------------

@app.route("/api/admin/download-db", methods=["GET"])
@requires_role('owner', 'admin')
def api_admin_download_db():
    """Stáhne aktuální SQLite databázi jako soubor (pouze owner/admin)."""
    db_path = os.environ.get("DB_PATH") or "/var/data/app.db"
    if not os.path.exists(db_path):
        return jsonify({"ok": False, "error": "db_not_found", "path": db_path}), 404
    return send_file(db_path, as_attachment=True, download_name="app.db")

@app.route("/api/admin/export-all", methods=["GET"])
@requires_role('owner', 'admin')
def api_admin_export_all():
    """Export všech tabulek do JSON (pouze owner/admin)."""
    db = get_db()
    tables = [r["name"] for r in db.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name"
    ).fetchall()]
    export = {
        "exported_at": datetime.utcnow().isoformat() + "Z",
        "db_path": os.environ.get("DB_PATH") or "/var/data/app.db",
        "tables": {},
    }
    for t in tables:
        rows = db.execute(f"SELECT * FROM {t}").fetchall()
        export["tables"][t] = [dict(r) for r in rows]
    payload = json.dumps(export, ensure_ascii=False, indent=2)
    buf = io.BytesIO(payload.encode("utf-8"))
    filename = f"green-david-export-{datetime.utcnow().strftime('%Y%m%d-%H%M%S')}.json"
    return send_file(buf, mimetype="application/json", as_attachment=True, download_name=filename)




@app.route("/api/search", methods=["GET"])
def api_search():
    q = (request.args.get("q") or "").strip()
    if not q:
        return jsonify([])
    like = f"%{q}%"
    db = get_db()
    out = []
    try:
        # Use title column if available, fallback to name
        title_col = _job_title_col()
        cur = db.execute(f"SELECT id, {title_col} AS title, city, code, date FROM jobs WHERE ({title_col} LIKE ? COLLATE NOCASE OR city LIKE ? COLLATE NOCASE OR code LIKE ? COLLATE NOCASE) ORDER BY id DESC LIMIT 50", (like, like, like))
        for r in cur.fetchall():
            out.append({"type":"Zakázka","id":r["id"],"title":r["title"] or "", "sub":" • ".join([x for x in [r["city"], r["code"]] if x]),"date":r["date"],"url": f"/?tab=jobs&jobId={r['id']}"})
    except Exception: pass
    try:
        cur = db.execute("SELECT id, name, role FROM employees WHERE (name LIKE ? COLLATE NOCASE OR role LIKE ? COLLATE NOCASE) ORDER BY id DESC LIMIT 50", (like, like))
        for r in cur.fetchall():
            out.append({"type":"Zaměstnanec","id":r["id"],"title":r["name"],"sub":r["role"] or "","date":"","url": "/?tab=employees"})
    except Exception: pass
    return jsonify(out)

@app.route("/search", methods=["GET"])
def search_page():
    q = (request.args.get("q") or "").strip()
    results = []
    if q:
        like = f"%{q}%"
        db = get_db()
        try:
            # Use title column if available, fallback to name
            title_col = _job_title_col()
            cur = db.execute(f"SELECT id, {title_col} AS title, city, code, date FROM jobs WHERE ({title_col} LIKE ? COLLATE NOCASE OR city LIKE ? COLLATE NOCASE OR code LIKE ? COLLATE NOCASE) ORDER BY id DESC LIMIT 50", (like, like, like))
            for r in cur.fetchall():
                results.append({"type":"Zakázka","id":r["id"],"title":r["title"] or "", "sub":" • ".join([x for x in [r["city"], r["code"]] if x]),"date":r["date"],"url": f"/?tab=jobs&jobId={r['id']}"})
        except Exception: pass
        try:
            cur = db.execute("SELECT id, name, role FROM employees WHERE (name LIKE ? COLLATE NOCASE OR role LIKE ? COLLATE NOCASE) ORDER BY id DESC LIMIT 50", (like, like))
            for r in cur.fetchall():
                results.append({"type":"Zaměstnanec","id":r["id"],"title":r["name"],"sub":r["role"] or "","date":"","url": "/?tab=employees"})
        except Exception: pass
    return render_template("search.html", title="Hledání", q=q, results=results)

# ----------------- Calendar API -----------------
@app.route("/api/calendar", methods=["GET", "POST", "PATCH"])
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

@app.route("/api/calendar/<int:event_id>", methods=["DELETE"])
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
@app.route("/gd/api/jobs", methods=["GET", "POST", "PATCH", "DELETE"])
def gd_api_jobs():
    return api_jobs()

@app.route("/gd/api/jobs/<int:job_id>", methods=["GET"])
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

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route("/api/tasks/<int:task_id>/attachments", methods=["GET", "POST", "DELETE"])
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

@app.route("/api/issues/<int:issue_id>/attachments", methods=["GET", "POST", "DELETE"])
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
@app.route("/api/attachments/<path:filename>")
def download_attachment(filename):
    return send_from_directory(UPLOAD_FOLDER, filename, as_attachment=True)

# === COMMENTS API ===
@app.route("/api/tasks/<int:task_id>/comments", methods=["GET", "POST"])
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

@app.route("/api/issues/<int:issue_id>/comments", methods=["GET", "POST"])
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
@app.route("/api/tasks/<int:task_id>/location", methods=["GET", "POST", "DELETE"])
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

@app.route("/api/issues/<int:issue_id>/location", methods=["GET", "POST", "DELETE"])
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

@app.route("/gd/api/tasks", methods=["GET", "POST", "PATCH", "PUT", "DELETE"])
def gd_api_tasks():
    return api_tasks()

@app.route("/gd/api/employees", methods=["GET", "POST", "PATCH", "DELETE"])
def gd_api_employees():
    return api_employees()

@app.route("/gd/api/timesheets", methods=["GET", "POST", "PATCH", "DELETE"])
def gd_api_timesheets():
    return api_timesheets()

@app.route("/gd/api/calendar", methods=["GET", "POST", "PATCH"])
def gd_api_calendar():
    return api_calendar()

@app.route("/gd/api/calendar/<int:event_id>", methods=["DELETE"])
def gd_api_calendar_delete(event_id):
    return api_calendar_delete(event_id)


# ----------------- run -----------------


@app.route("/api/_routes", methods=["GET"])
def api_routes():
    """Debug helper: returns registered routes so you can verify endpoints exist."""
    try:
        routes = []
        for rule in app.url_map.iter_rules():
            if rule.endpoint == 'static':
                continue
            routes.append({
                "rule": str(rule),
                "methods": sorted([m for m in rule.methods if m not in ("HEAD","OPTIONS")]),
                "endpoint": rule.endpoint,
            })
        return jsonify({"ok": True, "routes": sorted(routes, key=lambda r: r["rule"])})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


if __name__ == "__main__":
    # Pro lokální vývoj použij 127.0.0.1, pro Render použij 0.0.0.0
    is_render = os.environ.get("RENDER") or os.environ.get("RENDER_EXTERNAL_HOSTNAME")
    host = "0.0.0.0" if is_render else "127.0.0.1"
    port = int(os.environ.get("PORT", 5000))
    debug = not is_render  # Debug mode jen lokálně
    
    print(f"[Server] Starting Flask app on {host}:{port} (debug={debug})")
    app.run(host=host, port=port, debug=debug)



# ============================================================================
# FILE ATTACHMENTS AND GPS LOCATION API ENDPOINTS
# ============================================================================

ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif', 'doc', 'docx', 'xls', 'xlsx', 'zip', 'mp4', 'mov'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route("/api/tasks/<int:task_id>/attachments", methods=["GET", "POST", "DELETE"])
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
            filepath = os.path.join(UPLOAD_DIR, filename)
            
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

@app.route("/api/issues/<int:issue_id>/attachments", methods=["GET", "POST", "DELETE"])
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
            filepath = os.path.join(UPLOAD_DIR, filename)
            
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

@app.route("/api/attachments/<path:filename>")
def download_attachment(filename):
    return send_from_directory(UPLOAD_DIR, filename, as_attachment=True)

@app.route("/api/tasks/<int:task_id>/location", methods=["GET", "POST", "DELETE"])
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
        
        db.execute("DELETE FROM task_locations WHERE task_id = ?", (task_id,))
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

@app.route("/api/issues/<int:issue_id>/location", methods=["GET", "POST", "DELETE"])
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
        
        db.execute("DELETE FROM issue_locations WHERE issue_id = ?", (issue_id,))
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

