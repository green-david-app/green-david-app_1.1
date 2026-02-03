"""
Permission Map pro Role-Based Access Control (RBAC)

Definuje oprávnění pro každou roli v systému.
"""

# Role Enum (kompatibilní s existujícími rolemi)
class UserRole:
    DIRECTOR = 'director'      # Plný přístup, finance, strategická rozhodnutí
    MANAGER = 'manager'        # Operativní řízení, plánování, přehled zakázek
    LANDER = 'lander'          # Vedoucí party v terénu, koordinace týmu
    WORKER = 'worker'          # Základní pracovník, logování práce
    
    # Legacy role pro kompatibilitu
    OWNER = 'owner'            # Mapuje na director
    TEAM_LEAD = 'team_lead'    # Mapuje na lander
    ADMIN = 'admin'            # Mapuje na director

# Mapování starých rolí na nové
ROLE_MAPPING = {
    'owner': 'director',
    'admin': 'director',
    'team_lead': 'lander',
    'manager': 'manager',
    'worker': 'worker',
    'director': 'director',
    'lander': 'lander'
}

# Permission Map - oprávnění pro každou roli
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

def normalize_role(role):
    """Normalizuje roli - mapuje staré role na nové."""
    if not role:
        return 'worker'
    role_lower = role.lower()
    return ROLE_MAPPING.get(role_lower, role_lower)

def get_role_permissions(role):
    """Vrátí seznam oprávnění pro danou roli."""
    normalized_role = normalize_role(role)
    return ROLE_PERMISSIONS.get(normalized_role, [])

def has_permission(role, permission):
    """Zkontroluje, zda má role dané oprávnění."""
    permissions = get_role_permissions(role)
    return permission in permissions
