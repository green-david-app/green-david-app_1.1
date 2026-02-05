# Green David App
from flask import Blueprint, jsonify, request, session
from werkzeug.security import check_password_hash, generate_password_hash
from app.database import get_db
from app.utils.permissions import current_user

auth_bp = Blueprint('auth', __name__)


@auth_bp.route("/api/me")
def api_me():
    u = current_user()
    unread = 0
    emp = None
    if u:
        try:
            db = get_db()
            # Current employee mapping (optional)
            try:
                erow = db.execute(
                    "SELECT id, name, role FROM employees WHERE user_id=? LIMIT 1",
                    (int(u["id"]),),
                ).fetchone()
                if erow:
                    emp = {"id": int(erow["id"]), "name": erow["name"], "role": erow["role"]}
                    # Backward-compatible field used by some frontends
                    u["employee_id"] = emp["id"]
            except Exception:
                emp = None
            # Prefer user_id binding; fallback also checks employee mapping.
            # NOTE: notifications table is created in ensure_schema; if legacy DB lacks it, this is safe.
            unread = db.execute(
                "SELECT COUNT(1) FROM notifications WHERE (user_id=? OR employee_id IN (SELECT id FROM employees WHERE user_id=?)) AND is_read=0",
                (int(u["id"]), int(u["id"])),
            ).fetchone()[0]
            unread = int(unread or 0)
        except Exception:
            unread = 0
    return jsonify({"ok": True, "authenticated": bool(u), "user": u, "employee": emp, "tasks_count": 0, "unread_notifications": unread})


@auth_bp.route("/api/login", methods=["POST"])
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


@auth_bp.route("/api/logout", methods=["POST"])
def api_logout():
    # remove user id from session
    session.pop("uid", None)
    return jsonify({"ok": True})
