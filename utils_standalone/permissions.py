"""
Standalone permissions - funguje BEZ flask_sqlalchemy.
Bezpečný default: pokud nejde zjistit roli → worker (nejméně oprávnění).

Synchronizováno s config/permissions.py
"""

# Mapování starých rolí na nové (stejné jako v config/permissions.py)
ROLE_MAPPING = {
    'owner': 'director',
    'admin': 'director',
    'team_lead': 'lander',
    'manager': 'manager',
    'worker': 'worker',
    'director': 'director',
    'lander': 'lander'
}

# Permission Map - oprávnění pro každou roli (stejné jako v config/permissions.py)
ROLE_PERMISSIONS = {
    'director': [
        'view_finance', 'edit_finance',
        'edit_plan', 'approve_plan',
        'assign_people', 'manage_users',
        'log_work', 'log_material', 'add_photo',
        'create_blocker', 'approve_changes',
        'view_reports', 'export_data'
    ],
    'manager': [
        'view_finance',  # pouze čtení
        'edit_plan',
        'assign_people',
        'log_work', 'log_material', 'add_photo',
        'create_blocker', 'approve_changes',
        'view_reports'
    ],
    'lander': [
        'assign_people',  # pouze v rámci své party
        'log_work', 'log_material', 'add_photo',
        'create_blocker',
        'view_team_tasks'
    ],
    'worker': [
        'log_work', 'add_photo',
        'create_blocker',
        'view_my_tasks'
    ]
}

# Legacy role 'owner' mapuje na director
ROLE_PERMISSIONS['owner'] = ROLE_PERMISSIONS['director']


def normalize_role(role):
    """Normalizuje roli - mapuje staré role na nové."""
    if not role:
        return 'worker'
    role_lower = role.lower()
    return ROLE_MAPPING.get(role_lower, role_lower)


def _get_role():
    """Zjistí roli - bezpečný fallback na 'worker'."""
    try:
        from flask_login import current_user
        if current_user and current_user.is_authenticated:
            role = getattr(current_user, 'role', None)
            if role:
                return normalize_role(role)
    except Exception:
        pass
    
    try:
        from flask import session
        role = session.get('user_role')
        if role:
            return normalize_role(role)
    except Exception:
        pass
    
    return 'worker'  # Bezpečný default - nejméně oprávnění


def has_permission(permission):
    """Zkontroluje, zda má aktuální uživatel dané oprávnění."""
    role = _get_role()
    permissions = ROLE_PERMISSIONS.get(role, ROLE_PERMISSIONS['worker'])
    return permission in permissions


def get_user_role():
    """Vrátí roli aktuálního uživatele."""
    return _get_role()


def require_permission(permission):
    """Dekorátor pro ochranu API endpoints - vyžaduje dané oprávnění."""
    from functools import wraps
    
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            from flask import jsonify, session
            
            # Zkontroluj autentizaci
            if not session.get('uid'):
                return jsonify({'ok': False, 'error': 'Nepřihlášen'}), 401
            
            # Zkontroluj oprávnění
            if not has_permission(permission):
                return jsonify({'ok': False, 'error': 'Nedostatečná oprávnění'}), 403
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator


def inject_permissions():
    """Context processor pro templates - vloží permission funkce."""
    try:
        from flask import session
        user_id = session.get('uid')
        user_role = _get_role()
    except Exception:
        user_id = None
        user_role = 'worker'
    
    # Zkus získat user objekt a unread count (volitelné)
    user = None
    unread_count = 0
    
    try:
        from flask import g
        from main import get_db
        
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
    except Exception:
        # Pokud DB není dostupná, pokračuj bez user objektu
        pass
    
    # Zkus získat mobile_mode (volitelné)
    try:
        from app.utils.mobile_mode import get_mobile_mode_for_template
        mobile_mode = get_mobile_mode_for_template()
    except Exception:
        mobile_mode = 'field'
    
    return {
        'user_role': user_role,
        'has_perm': has_permission,
        'normalize_role': normalize_role,
        'mobile_mode': mobile_mode,
        'user': user,
        'unread_count': unread_count
    }
