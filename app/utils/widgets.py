"""
Widget System - Rendering a filtrování widgetů

Poskytuje funkce pro získání widgetů pro uživatele podle role, módu a oprávnění.
"""

import json
import sys
import os
from flask import session

# Přidat root directory do path pro import config
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

try:
    from config.widgets import WIDGET_REGISTRY, get_role_default_widgets
    from config.permissions import normalize_role
    from app.utils.permissions import has_permission
except ImportError:
    # Fallback pokud moduly nejsou dostupné
    WIDGET_REGISTRY = {}
    def get_role_default_widgets(role, mode):
        return []
    def normalize_role(role):
        return role or 'worker'
    def has_permission(permission):
        return False


def get_user_widgets(user_id, role, mode):
    """Vrátí seznam widgetů pro uživatele a režim."""
    # Pokud není user_id, vrať demo widgety
    if not user_id:
        if mode == 'field':
            return ['current_job', 'quick_log', 'my_tasks', 'add_photo', 'report_blocker', 'offline_status']
        else:
            return ['notifications', 'jobs_risk', 'overdue_jobs', 'team_load', 'stock_alerts', 'budget_burn']
    
    try:
        from main import get_db
        db = get_db()
        
        # 1. Zkus user override
        layout_row = db.execute(
            "SELECT field_widgets, full_widgets FROM user_dashboard_layout WHERE user_id = ?",
            (user_id,)
        ).fetchone()
        
        if layout_row:
            widgets_json = layout_row[0] if mode == 'field' else layout_row[1]
            if widgets_json:
                try:
                    widget_ids = json.loads(widgets_json)
                    if widget_ids:
                        return filter_accessible_widgets(widget_ids, role, mode)
                except (json.JSONDecodeError, TypeError):
                    pass
        
        # 2. Fallback na role default
        normalized_role = normalize_role(role)
        default_widgets = get_role_default_widgets(normalized_role, mode)
        return filter_accessible_widgets(default_widgets, role, mode)
        
    except Exception as e:
        print(f"[ERROR] Failed to get user widgets: {e}")
        # Fallback na role default nebo demo widgety
        if not user_id:
            if mode == 'field':
                return ['current_job', 'quick_log', 'my_tasks', 'add_photo', 'report_blocker', 'offline_status']
            else:
                return ['notifications', 'jobs_risk', 'overdue_jobs', 'team_load', 'stock_alerts', 'budget_burn']
        normalized_role = normalize_role(role)
        default_widgets = get_role_default_widgets(normalized_role, mode)
        return filter_accessible_widgets(default_widgets, role, mode)


def filter_accessible_widgets(widget_ids, role, mode):
    """Filtruje widgety podle oprávnění a režimu."""
    result = []
    normalized_role = normalize_role(role)
    
    for widget_id in widget_ids:
        widget = WIDGET_REGISTRY.get(widget_id)
        if not widget:
            continue
        
        # Kontrola režimu
        if mode not in widget.get('supported_modes', []):
            continue
        
        # Kontrola role
        if normalized_role not in widget.get('supported_roles', []):
            continue
        
        # Kontrola oprávnění
        required_perms = widget.get('required_perms', [])
        if required_perms:
            if not all(has_permission(p) for p in required_perms):
                continue
        
        result.append(widget_id)
    
    return result


def save_user_widgets(user_id, mode, widget_ids):
    """Uloží widget layout pro uživatele."""
    try:
        from main import get_db
        db = get_db()
        
        widgets_json = json.dumps(widget_ids)
        field_column = 'field_widgets' if mode == 'field' else 'full_widgets'
        other_column = 'full_widgets' if mode == 'field' else 'field_widgets'
        
        # Zkontroluj, zda už existuje záznam
        existing = db.execute(
            "SELECT id FROM user_dashboard_layout WHERE user_id = ?",
            (user_id,)
        ).fetchone()
        
        if existing:
            # Update existujícího záznamu
            db.execute(
                f"UPDATE user_dashboard_layout SET {field_column} = ?, updated_at = datetime('now') WHERE user_id = ?",
                (widgets_json, user_id)
            )
        else:
            # Vytvoř nový záznam - načti druhý sloupec jako prázdný array
            db.execute(
                f"INSERT INTO user_dashboard_layout (user_id, {field_column}, {other_column}, updated_at) VALUES (?, ?, '[]', datetime('now'))",
                (user_id, widgets_json)
            )
        
        db.commit()
        return True
    except Exception as e:
        print(f"[ERROR] Failed to save user widgets: {e}")
        return False


def get_available_widgets_for_user(role, mode):
    """Vrátí všechny dostupné widgety pro uživatele (pro editor)."""
    normalized_role = normalize_role(role)
    available = []
    
    for widget_id, widget in WIDGET_REGISTRY.items():
        # Kontrola režimu
        if mode not in widget.get('supported_modes', []):
            continue
        
        # Kontrola role
        if normalized_role not in widget.get('supported_roles', []):
            continue
        
        # Kontrola oprávnění
        required_perms = widget.get('required_perms', [])
        if required_perms:
            if not all(has_permission(p) for p in required_perms):
                continue
        
        available.append(widget_id)
    
    # Seřadit podle priority
    available.sort(key=lambda w_id: WIDGET_REGISTRY[w_id].get('priority', 999))
    
    return available
