"""
Mobile Mode Detection a Management

Určuje mobilní režim podle preference uživatele, role a viewport.
"""

from flask import session
from config.permissions import normalize_role


def get_user_setting(setting_key, default=None):
    """Získá nastavení uživatele z databáze."""
    try:
        from flask import g
        if not hasattr(g, 'db'):
            from main import get_db
            g.db = get_db()
        db = g.db
    except Exception:
        from main import get_db
        db = get_db()
    
    user_id = session.get('uid')
    if not user_id:
        return default
    
    try:
        result = db.execute(
            "SELECT {} FROM user_settings WHERE user_id = ?".format(setting_key),
            (user_id,)
        ).fetchone()
        
        if result and result[0] is not None:
            return result[0]
        return default
    except Exception:
        return default


def set_user_setting(setting_key, value):
    """Nastaví hodnotu nastavení uživatele."""
    try:
        from flask import g
        if not hasattr(g, 'db'):
            from main import get_db
            g.db = get_db()
        db = g.db
    except Exception:
        from main import get_db
        db = get_db()
    
    user_id = session.get('uid')
    if not user_id:
        return False
    
    try:
        # Zkontroluj, zda už existuje záznam
        existing = db.execute(
            "SELECT id FROM user_settings WHERE user_id = ?",
            (user_id,)
        ).fetchone()
        
        if existing:
            # Update existujícího záznamu
            db.execute(
                f"UPDATE user_settings SET {setting_key} = ?, updated_at = datetime('now') WHERE user_id = ?",
                (value, user_id)
            )
        else:
            # Vytvoř nový záznam
            db.execute(
                f"INSERT INTO user_settings (user_id, {setting_key}, updated_at) VALUES (?, ?, datetime('now'))",
                (user_id, value)
            )
        
        db.commit()
        return True
    except Exception as e:
        print(f"[ERROR] Failed to set user setting: {e}")
        return False


def get_mobile_mode():
    """Určí mobilní režim podle preference, role a viewport."""
    # Pokud není přihlášen, vrať field jako default
    if not session.get('uid'):
        return 'field'
    
    # 1. Explicitní preference uživatele
    user_pref = get_user_setting('mobile_mode', 'auto')
    if user_pref in ['field', 'full']:
        return user_pref
    
    # 2. Auto podle role
    role = normalize_role(session.get('user_role', 'worker'))
    role_defaults = {
        'director': 'full',
        'manager': 'full',
        'lander': 'field',
        'worker': 'field'
    }
    return role_defaults.get(role, 'field')


def get_mobile_mode_for_template():
    """Vrátí mobile mode pro použití v template."""
    return get_mobile_mode()
