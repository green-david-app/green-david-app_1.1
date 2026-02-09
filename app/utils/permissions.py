# Green David App
from flask import session, jsonify
from functools import wraps
from app.database import get_db
from app.config import ROLES, WRITE_ROLES, EMPLOYEE_ROLES


def normalize_role(role):
    """Normalizace role pro zpětnou kompatibilitu a konzistentní autorizaci."""
    if not role:
        return "owner"
    role = str(role).strip().lower()
    if role == "team_lead":
        return "lander"
    return role


def normalize_employee_role(role: str) -> str:
    """Normalizace role zaměstnance.

    - zachová kompatibilitu se staršími hodnotami (admin -> owner, team_lead -> lander)
    - pokud je hodnota neznámá, vrací 'worker'
    """
    if not role:
        return "worker"
    r = str(role).strip().lower()
    if r in ("admin",):
        r = "owner"
    if r == "team_lead":
        r = "lander"
    return r if r in EMPLOYEE_ROLES else "worker"


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
