"""
Widget Registry a Role Defaults

Definuje všechny dostupné widgety a jejich výchozí rozložení podle rolí.
"""

WIDGET_REGISTRY = {
    # === FIELD MODE WIDGETS ===
    'current_job': {
        'title': 'Aktuální zakázka',
        'template': 'widgets/current_job.html',
        'required_perms': [],
        'supported_modes': ['field', 'full'],
        'supported_roles': ['director', 'manager', 'lander', 'worker'],
        'data_endpoint': '/api/widgets/current-job',
        'size': 'full',  # full, half, quarter
        'priority': 1
    },
    'quick_log': {
        'title': 'Rychlý zápis',
        'template': 'widgets/quick_log.html',
        'required_perms': ['log_work'],
        'supported_modes': ['field'],
        'supported_roles': ['lander', 'worker'],
        'data_endpoint': None,
        'size': 'full',
        'priority': 2
    },
    'my_tasks': {
        'title': 'Moje úkoly dnes',
        'template': 'widgets/my_tasks.html',
        'required_perms': ['view_my_tasks'],
        'supported_modes': ['field', 'full'],
        'supported_roles': ['director', 'manager', 'lander', 'worker'],
        'data_endpoint': '/api/widgets/my-tasks',
        'size': 'full',
        'priority': 3
    },
    'add_photo': {
        'title': 'Přidat foto',
        'template': 'widgets/add_photo.html',
        'required_perms': ['add_photo'],
        'supported_modes': ['field'],
        'supported_roles': ['lander', 'worker'],
        'data_endpoint': None,
        'size': 'half',
        'priority': 4
    },
    'material_quick': {
        'title': 'Výdej materiálu',
        'template': 'widgets/material_quick.html',
        'required_perms': ['log_material'],
        'supported_modes': ['field'],
        'supported_roles': ['lander', 'worker'],
        'data_endpoint': '/api/widgets/materials',
        'size': 'half',
        'priority': 5
    },
    'report_blocker': {
        'title': 'Nahlásit problém',
        'template': 'widgets/report_blocker.html',
        'required_perms': ['create_blocker'],
        'supported_modes': ['field', 'full'],
        'supported_roles': ['director', 'manager', 'lander', 'worker'],
        'data_endpoint': None,
        'size': 'half',
        'priority': 6
    },
    'offline_status': {
        'title': 'Stav synchronizace',
        'template': 'widgets/offline_status.html',
        'required_perms': [],
        'supported_modes': ['field'],
        'supported_roles': ['lander', 'worker'],
        'data_endpoint': None,
        'size': 'quarter',
        'priority': 10
    },
    
    # === FULL MODE WIDGETS ===
    'notifications': {
        'title': 'Oznámení',
        'template': 'widgets/notifications.html',
        'required_perms': [],
        'supported_modes': ['full'],
        'supported_roles': ['director', 'manager', 'lander'],
        'data_endpoint': '/api/widgets/notifications',
        'size': 'full',
        'priority': 1
    },
    'jobs_risk': {
        'title': 'Rizikové zakázky',
        'template': 'widgets/jobs_risk.html',
        'required_perms': ['view_reports'],
        'supported_modes': ['full'],
        'supported_roles': ['director', 'manager'],
        'data_endpoint': '/api/widgets/jobs-risk',
        'size': 'full',
        'priority': 2
    },
    'overdue_jobs': {
        'title': 'Zpožděné zakázky',
        'template': 'widgets/overdue_jobs.html',
        'required_perms': ['view_reports'],
        'supported_modes': ['full'],
        'supported_roles': ['director', 'manager'],
        'data_endpoint': '/api/widgets/overdue-jobs',
        'size': 'half',
        'priority': 3
    },
    'team_load': {
        'title': 'Vytížení týmu',
        'template': 'widgets/team_load.html',
        'required_perms': ['assign_people'],
        'supported_modes': ['full'],
        'supported_roles': ['director', 'manager'],
        'data_endpoint': '/api/widgets/team-load',
        'size': 'half',
        'priority': 4
    },
    'stock_alerts': {
        'title': 'Skladové výstrahy',
        'template': 'widgets/stock_alerts.html',
        'required_perms': ['log_material'],
        'supported_modes': ['full'],
        'supported_roles': ['director', 'manager', 'lander'],
        'data_endpoint': '/api/widgets/stock-alerts',
        'size': 'half',
        'priority': 5
    },
    'budget_burn': {
        'title': 'Čerpání rozpočtu',
        'template': 'widgets/budget_burn.html',
        'required_perms': ['view_finance'],
        'supported_modes': ['full'],
        'supported_roles': ['director', 'manager'],
        'data_endpoint': '/api/widgets/budget-burn',
        'size': 'half',
        'priority': 6
    }
}

# Role Defaults - výchozí widgety pro každou roli a mód
ROLE_DEFAULT_WIDGETS = {
    'director': {
        'field': ['current_job', 'my_tasks', 'report_blocker'],
        'full': ['notifications', 'jobs_risk', 'overdue_jobs', 'team_load', 'budget_burn', 'stock_alerts']
    },
    'manager': {
        'field': ['current_job', 'my_tasks', 'quick_log', 'report_blocker'],
        'full': ['notifications', 'jobs_risk', 'overdue_jobs', 'team_load', 'stock_alerts']
    },
    'lander': {
        'field': ['current_job', 'quick_log', 'my_tasks', 'add_photo', 'material_quick', 'report_blocker', 'offline_status'],
        'full': ['notifications', 'my_tasks', 'stock_alerts']
    },
    'worker': {
        'field': ['current_job', 'quick_log', 'my_tasks', 'add_photo', 'report_blocker', 'offline_status'],
        'full': ['my_tasks', 'notifications']
    }
}

def get_widget(widget_id):
    """Vrátí widget definici podle ID."""
    return WIDGET_REGISTRY.get(widget_id)

def get_all_widgets():
    """Vrátí všechny dostupné widgety."""
    return WIDGET_REGISTRY

def get_role_default_widgets(role, mode):
    """Vrátí výchozí widgety pro roli a mód."""
    normalized_role = role.lower()
    if normalized_role not in ROLE_DEFAULT_WIDGETS:
        return []
    return ROLE_DEFAULT_WIDGETS[normalized_role].get(mode, [])
