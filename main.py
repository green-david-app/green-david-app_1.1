
from flask import Flask, Blueprint, jsonify, request, render_template, session, abort, redirect
from jinja2 import TemplateNotFound
import sqlite3, os, datetime

app = Flask(__name__)

# --- Compatibility helpers expected by wsgi/gd_calendar_hotfix ---
def require_role(*expected_roles):
    def decorator(f):
        def wrapped(*args, **kwargs):
            # role = session.get('role')  # pokud budeš chtít zpřísnit, odkomentuj a doplň klíč
            # if expected_roles and role not in expected_roles:
            #     return abort(403)
            return f(*args, **kwargs)
        wrapped.__name__ = f.__name__
        return wrapped
    return decorator

def _normalize_date(s):
    if not s:
        return s
    s = str(s).strip()
    try:
        dt = datetime.datetime.strptime(s, '%Y-%m-%d').date()
        return dt.isoformat()
    except Exception:
        pass
    for fmt in ('%d.%m.%Y', '%-d.%-m.%Y', '%d.%m.%y'):
        try:
            dt = datetime.datetime.strptime(s, fmt).date()
            return dt.isoformat()
        except Exception:
            continue
    return s
# --- /compatibility ---

# --------- Brigádníci API ---------
def get_db():
    DB_PATH = os.environ.get('GD_DB_PATH', 'app.db')
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    return con

api_bp = Blueprint('gd_brigadnici_api', __name__)

@api_bp.route('/gd/api/brigadnici', methods=['GET','POST'])
def brigadnici_collection():
    con = get_db()
    cur = con.cursor()
    cur.execute('CREATE TABLE IF NOT EXISTS brigadnici (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL, role TEXT)')
    con.commit()
    if request.method == 'POST':
        data = request.get_json(force=True) or {}
        name = (data.get('name') or '').strip()
        role = (data.get('role') or 'Brigádník').strip()
        if not name:
            return jsonify({'error':'name required'}), 400
        cur.execute('INSERT INTO brigadnici (name, role) VALUES (?, ?)', (name, role))
        con.commit()
        return jsonify({'ok':True}), 201
    rows = cur.execute('SELECT id, name, role FROM brigadnici ORDER BY id DESC').fetchall()
    return jsonify([dict(r) for r in rows])

@api_bp.route('/gd/api/brigadnici/<int:bid>', methods=['DELETE'])
def brigadnik_delete(bid):
    con = get_db()
    cur = con.cursor()
    cur.execute('DELETE FROM brigadnici WHERE id=?', (bid,))
    con.commit()
    return jsonify({'ok':True})

app.register_blueprint(api_bp)
# --------- /Brigádníci API ---------

# --------- Employees page aliases (navbar-safe) ---------
@app.route('/zamestnanci')
@app.route('/zamestnanci/')
@app.route('/employees')
@app.route('/employees/')
@app.route('/employee')
@app.route('/staff')
def employees_page():
    return render_template('employees.html')
# --------- /Employees aliases ---------

# --------- Root '/' handler (fix 404) ---------
@app.route('/')
def root():
    # Preferuj index.html, jinak přesměruj na kalendář
    try:
        return render_template('index.html')
    except TemplateNotFound:
        return redirect('/calendar')
# --------- /root ---------
