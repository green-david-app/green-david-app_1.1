import os, re, io, sqlite3, json
from datetime import datetime, date, timedelta
from flask import Flask, abort, g, jsonify, render_template, request, send_file, send_from_directory, session, redirect
from werkzeug.security import generate_password_hash, check_password_hash
from assignment_helpers import (
    assign_employees_to_task, assign_employees_to_issue,
    get_task_assignees, get_issue_assignees,
    get_employee_tasks, get_employee_issues
)
from app.config import (
    DATABASE as DB_PATH, SECRET_KEY, UPLOAD_FOLDER as UPLOAD_DIR,
    ROLES, WRITE_ROLES, EMPLOYEE_ROLES, SEND_FILE_MAX_AGE_DEFAULT
)
from app.database import get_db, close_db, _table_has_column, _table_exists
from app.utils.migrations import (
    apply_migrations, ensure_schema,
    _migrate_completed_at, _migrate_employees_enhanced,
    _migrate_roles_and_hierarchy, _migrate_crew_control_tables,
    seed_admin, _auto_upgrade_admins_to_owner, seed_employees, seed_plant_catalog
)
from app.utils.permissions import (
    normalize_role, normalize_employee_role, current_user,
    require_auth, require_role, requires_role, get_current_user, can_manage_employee
)
from app.utils.helpers import (
    audit_event, _employee_user_id, create_notification,
    _expand_assignees_with_delegate, _notify_assignees, _normalize_date,
    _jobs_info, _job_title_col, _job_select_all, _job_insert_cols_and_vals, _job_title_update_set
)

# Crew Control System API
try:
    from crew_api import crew_bp
    CREW_API_AVAILABLE = True
except ImportError:
    CREW_API_AVAILABLE = False
    print("[INFO] Crew API module not available")

# Import route blueprints
from app.routes.auth import auth_bp
from app.routes.notifications import notifications_bp
from app.routes.employees import employees_bp
from app.routes.jobs import jobs_bp
from app.routes.tasks import tasks_bp
from app.routes.timesheets import timesheets_bp
from app.routes.calendar_routes import calendar_bp
from app.routes.warehouse import warehouse_bp
from app.routes.planning import planning_bp
from app.routes.reports import reports_bp
from app.routes.nursery import nursery_bp
from app.routes.settings import settings_bp
from app.routes.mobile import mobile_bp
from app.routes.finance import finance_bp
from app.routes.documents import documents_bp
from app.routes.notes import notes_bp
from app.routes.budget import budget_bp
from app.routes.api import api_bp
from app.routes.parties import parties_bp

app = Flask(__name__, static_folder=".", static_url_path="")
# Disable aggressive caching in development so UI settings (language/theme) apply immediately
app.config["SEND_FILE_MAX_AGE_DEFAULT"] = SEND_FILE_MAX_AGE_DEFAULT

# Register blueprints
app.register_blueprint(auth_bp)
app.register_blueprint(notifications_bp)
app.register_blueprint(employees_bp)
app.register_blueprint(jobs_bp)
app.register_blueprint(tasks_bp)
app.register_blueprint(timesheets_bp)
app.register_blueprint(calendar_bp)
app.register_blueprint(warehouse_bp)
app.register_blueprint(planning_bp)
app.register_blueprint(reports_bp)
app.register_blueprint(nursery_bp)
app.register_blueprint(settings_bp)
app.register_blueprint(mobile_bp)
app.register_blueprint(finance_bp)
app.register_blueprint(documents_bp)
app.register_blueprint(notes_bp)
app.register_blueprint(budget_bp)
app.register_blueprint(api_bp)
app.register_blueprint(parties_bp)

# Register Crew Control System API blueprint
if CREW_API_AVAILABLE:
    app.register_blueprint(crew_bp)
    print("[INFO] Crew Control System API registered")

@app.after_request
def _disable_cache_for_static(resp):
    try:
        path = request.path or ""
        if path.startswith("/static/") or path.endswith(".js") or path.endswith(".css"):
            resp.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
            resp.headers["Pragma"] = "no-cache"
            resp.headers["Expires"] = "0"
        # Service Worker needs proper scope header
        if path == "/sw.js":
            resp.headers["Service-Worker-Allowed"] = "/"
    except Exception:
        pass
    return resp

app.secret_key = SECRET_KEY

# ----------------- Database utilities -----------------
# Database functions are imported from app.database

@app.teardown_appcontext
def teardown_db(exception=None):
    """Close the database connection at the end of the request."""
    close_db(exception)

# Helper functions are imported from app.utils.helpers and app.utils.permissions


@app.before_request
def _ensure():
    """Run migrations and seed data on startup"""
    from app.utils.migrations import _ensure as _run_migrations
    _run_migrations()

@app.route("/")
def index():
    # Detekce mobilu
    user_agent = request.headers.get('User-Agent', '').lower()
    is_mobile = any(x in user_agent for x in ['mobile', 'android', 'iphone', 'ipad'])
    
    if is_mobile:
        # Získej mobile mode
        try:
            from app.utils.mobile_mode import get_mobile_mode
            mobile_mode = get_mobile_mode()
        except:
            mobile_mode = request.cookies.get('mobile_mode', 'field')
        
        if mobile_mode == 'field':
            # FIELD mode = Jinja template
            return redirect('/mobile/today')
        else:
            # FULL mode = zobrazí DESKTOP stránku (s responsive CSS)
            return send_from_directory(".", "index.html")
    
    # Desktop
    return send_from_directory(".", "index.html")

# Work inbox (safe standalone page)
@app.route("/inbox")
@app.route("/inbox/")
@app.route("/inbox.html")
def work_inbox_page():
    return send_from_directory(".", "inbox.html")

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

if __name__ == "__main__":
    # Pro lokální vývoj použij 127.0.0.1, pro Render použij 0.0.0.0
    is_render = os.environ.get("RENDER") or os.environ.get("RENDER_EXTERNAL_HOSTNAME")
    host = "0.0.0.0" if is_render else "127.0.0.1"
    port = int(os.environ.get("PORT", 5000))
    debug = not is_render  # Debug mode jen lokálně
    
    print(f"[Server] Starting Flask app on {host}:{port} (debug={debug})")
    app.run(host=host, port=port, debug=debug)
