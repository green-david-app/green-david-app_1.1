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
    """Dekorátor pro ochranu routes - vyžaduje dané oprávnění."""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not has_permission(permission):
                abort(403)
            return f(*args, **kwargs)
        return decorated_function
    return decorator


def require_role(*allowed_roles):
    """Dekorátor pro ochranu routes - vyžaduje jednu z povolených rolí."""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            user_role = get_user_role()
            if not user_role or user_role not in allowed_roles:
                abort(403)
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
    
    return {
        'user_role': get_user_role(),
        'has_perm': has_permission,
        'normalize_role': normalize_role,
        'mobile_mode': mobile_mode
    }
