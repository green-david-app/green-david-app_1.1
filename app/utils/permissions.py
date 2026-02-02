"""
RBAC Helper funkce pro Flask aplikaci.

Poskytuje funkce pro kontrolu oprávnění v routes a templates.
"""

import sys
import os
from functools import wraps
from flask import g, abort, session

# Přidat root directory do path pro import config
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

try:
    from config.permissions import (
        normalize_role, 
        get_role_permissions, 
        has_permission as _has_permission
    )
except ImportError:
    # Fallback pokud config/permissions.py není dostupný
    def normalize_role(role):
        role_mapping = {
            'owner': 'director', 'admin': 'director',
            'team_lead': 'lander',
            'manager': 'manager', 'worker': 'worker'
        }
        if not role:
            return 'worker'
        return role_mapping.get(role.lower(), role.lower())
    
    def get_role_permissions(role):
        return []
    
    def _has_permission(role, permission):
        return False


def get_user_role():
    """Vrátí roli aktuálního uživatele z session."""
    if not session.get('uid'):
        return 'worker'  # Default role pro demo
    role = session.get('user_role', 'worker')
    return normalize_role(role)


def has_permission(permission):
    """Zkontroluje, zda má aktuální uživatel dané oprávnění."""
    role = get_user_role()
    if not role:
        return False
    return _has_permission(role, permission)


def require_permission(permission):
    """Dekorátor pro ochranu API endpoints - vyžaduje dané oprávnění."""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            from flask import jsonify
            # Zkontroluj autentizaci
            if not session.get('uid'):
                return jsonify({'ok': False, 'error': 'Nepřihlášen'}), 401
            # Zkontroluj oprávnění
            if not has_permission(permission):
                return jsonify({'ok': False, 'error': 'Nedostatečná oprávnění'}), 403
            return f(*args, **kwargs)
        return decorated_function
    return decorator


def require_role(*allowed_roles):
    """Dekorátor pro ochranu API endpoints - vyžaduje jednu z povolených rolí."""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            from flask import jsonify
            # Zkontroluj autentizaci
            if not session.get('uid'):
                return jsonify({'ok': False, 'error': 'Nepřihlášen'}), 401
            # Zkontroluj roli
            user_role = get_user_role()
            if not user_role or user_role not in allowed_roles:
                return jsonify({'ok': False, 'error': 'Nedostatečná oprávnění'}), 403
            return f(*args, **kwargs)
        return decorated_function
    return decorator


def inject_permissions():
    """Context processor pro templates - vloží permission funkce."""
    try:
        from app.utils.mobile_mode import get_mobile_mode_for_template
        mobile_mode = get_mobile_mode_for_template()
    except Exception:
        mobile_mode = 'field'
    
    # Získej user objekt a unread count
    user = None
    unread_count = 0
    
    try:
        from flask import session, g
        from main import get_db
        
        user_id = session.get('uid')
        if user_id:
            db = get_db()
            user_row = db.execute(
                "SELECT id, name, email, role FROM users WHERE id = ?",
                (user_id,)
            ).fetchone()
            
            if user_row:
                user = {
                    'id': user_row[0],
                    'name': user_row[1],
                    'email': user_row[2],
                    'role': user_row[3]
                }
                
                # Získej unread notifications count
                unread = db.execute(
                    "SELECT COUNT(*) as cnt FROM notifications WHERE user_id = ? AND (is_read = 0 OR is_read IS NULL)",
                    (user_id,)
                ).fetchone()
                unread_count = unread[0] if unread else 0
    except Exception as e:
        print(f"[inject_permissions] Error: {e}")
    
    return {
        'user_role': get_user_role(),
        'has_perm': has_permission,
        'normalize_role': normalize_role,
        'mobile_mode': mobile_mode,
        'user': user,
        'unread_count': unread_count
    }
