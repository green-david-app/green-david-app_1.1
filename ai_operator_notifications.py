"""
GREEN DAVID APP - AI OPERÁTOR RBAC & NOTIFIKACE
================================================
RBAC filtrování insightů podle role uživatele.
Notifikační systém (in-app + email digest).

Podle PRD specifikace sekce 2 (RBAC) a sekce 8 (Notifikace).

Autor: Green David s.r.o.
Verze: 1.0
"""

from flask import jsonify, request, session
from datetime import datetime, timedelta
from functools import wraps
import json
import sqlite3

# Reference na get_db - nastaví se z main.py
get_db = None

def get_db_with_row_factory():
    """Získej DB connection s row_factory pro dict přístup"""
    db = get_db()
    db.row_factory = sqlite3.Row
    return db


# =============================================================================
# RBAC - ROLE-BASED ACCESS CONTROL
# =============================================================================

# Typy insightů obsahující finanční data (citlivé)
FINANCIAL_INSIGHT_TYPES = [
    'BUDGET_OVERRUN_LABOR',
    'BUDGET_OVERRUN_MATERIAL',
    'COMPLETED_NOT_INVOICED',
    'INVENTORY_VARIANCE'
]

# Evidence keys obsahující citlivá data
SENSITIVE_EVIDENCE_KEYS = [
    'budget_labor', 'actual_labor_cost', 'budget_materials', 'actual_material_cost',
    'hourly_rate', 'salary', 'wage', 'cost', 'price', 'margin', 'profit',
    'invoice_amount', 'payment'
]

# Role hierarchie podle PRD
ROLE_PERMISSIONS = {
    'owner': {
        'see_all_insights': True,
        'see_financial': True,
        'see_wages': True,
        'approve_all_drafts': True,
        'see_all_employees': True
    },
    'admin': {
        'see_all_insights': True,
        'see_financial': True,
        'see_wages': True,
        'approve_all_drafts': True,
        'see_all_employees': True
    },
    'manager': {
        'see_all_insights': True,
        'see_financial': True,  # bez mezd podle nastavení
        'see_wages': False,
        'approve_all_drafts': False,  # jen provozní
        'see_all_employees': False  # jen své týmy
    },
    'lander': {
        'see_all_insights': False,
        'see_financial': False,
        'see_wages': False,
        'approve_all_drafts': False,
        'see_all_employees': False
    },
    'worker': {
        'see_all_insights': False,
        'see_financial': False,
        'see_wages': False,
        'approve_all_drafts': False,
        'see_all_employees': False
    }
}


def get_current_user_role():
    """Získej roli aktuálního uživatele"""
    uid = session.get('uid')
    if not uid:
        return None, None
    
    db = get_db_with_row_factory()
    user = db.execute('SELECT id, role, manager_id FROM users WHERE id = ?', (uid,)).fetchone()
    
    if not user:
        return None, None
    
    role = user['role'] or 'owner'  # fallback pro zpětnou kompatibilitu
    return role, user['id']


def get_user_team_ids(user_id):
    """Získej ID zaměstnanců v týmu uživatele (pro managery)"""
    db = get_db_with_row_factory()
    
    # Najdi zaměstnance kde manager_id = user_id
    team = db.execute('''
        SELECT id FROM employees WHERE manager_id = ?
        UNION
        SELECT id FROM users WHERE manager_id = ?
    ''', (user_id, user_id)).fetchall()
    
    return [t['id'] for t in team]


def get_user_job_ids(user_id):
    """Získej ID zakázek přiřazených uživateli"""
    db = get_db_with_row_factory()
    
    jobs = db.execute('''
        SELECT DISTINCT job_id FROM job_employees WHERE employee_id = ?
        UNION
        SELECT id FROM jobs WHERE project_manager_id = ?
    ''', (user_id, user_id)).fetchall()
    
    return [j['job_id'] if 'job_id' in j.keys() else j['id'] for j in jobs]


def filter_insight_for_role(insight, role, user_id):
    """
    Filtruj insight podle role uživatele.
    Vrací None pokud uživatel nemá přístup, jinak upravený insight.
    """
    permissions = ROLE_PERMISSIONS.get(role, ROLE_PERMISSIONS['worker'])
    
    # Owner/Admin vidí vše
    if permissions['see_all_insights']:
        # Ale worker nemá vidět mzdy ani u owner role pokud je to výslovně zakázáno
        if not permissions.get('see_wages', True):
            insight = anonymize_wages(insight)
        return insight
    
    insight_type = insight.get('type', '')
    entity_type = insight.get('entity_type', '')
    entity_id = insight.get('entity_id')
    
    # Worker vidí pouze insighty týkající se jeho úkolů/docházky
    if role == 'worker':
        # Povolené typy pro workera
        worker_allowed_types = [
            'TASK_OVERDUE',
            'EMPLOYEE_OVERLOAD',
            'EMPLOYEE_IDLE',
            'MISSING_PHOTO_DOC'
        ]
        
        if insight_type not in worker_allowed_types:
            return None
        
        # Musí se týkat jeho samotného
        if entity_type == 'employee' and entity_id != user_id:
            return None
        
        # Nebo jeho úkolů
        if entity_type == 'task':
            db = get_db_with_row_factory()
            task = db.execute('SELECT employee_id FROM tasks WHERE id = ?', (entity_id,)).fetchone()
            if not task or task['employee_id'] != user_id:
                return None
        
        # Anonymizuj finanční data
        insight = anonymize_financial(insight)
        return insight
    
    # Manager vidí provozní insighty pro své týmy
    if role == 'manager':
        # Skryj finanční insighty s mzdami
        if insight_type in FINANCIAL_INSIGHT_TYPES:
            insight = anonymize_wages(insight)
        
        # Filtruj podle týmu/zakázek
        team_ids = get_user_team_ids(user_id)
        job_ids = get_user_job_ids(user_id)
        
        if entity_type == 'employee' and entity_id not in team_ids:
            return None
        
        if entity_type == 'job' and entity_id not in job_ids:
            # Povolíme vidět pokud je to obecný insight
            pass
        
        return insight
    
    # Lander - podobné jako manager ale omezenější
    if role == 'lander':
        if insight_type in FINANCIAL_INSIGHT_TYPES:
            return None
        
        job_ids = get_user_job_ids(user_id)
        
        if entity_type == 'job' and entity_id not in job_ids:
            return None
        
        insight = anonymize_financial(insight)
        return insight
    
    return None


def anonymize_financial(insight):
    """Odstraň finanční údaje z insightu"""
    if not insight:
        return insight
    
    insight = dict(insight)
    
    # Anonymizuj evidence
    if 'evidence' in insight and isinstance(insight['evidence'], dict):
        for key in SENSITIVE_EVIDENCE_KEYS:
            if key in insight['evidence']:
                insight['evidence'][key] = '***'
    
    if 'evidence_json' in insight:
        try:
            evidence = json.loads(insight['evidence_json'])
            for key in SENSITIVE_EVIDENCE_KEYS:
                if key in evidence:
                    evidence[key] = '***'
            insight['evidence_json'] = json.dumps(evidence)
        except:
            pass
    
    return insight


def anonymize_wages(insight):
    """Odstraň pouze mzdové údaje (ne všechny finanční)"""
    if not insight:
        return insight
    
    insight = dict(insight)
    wage_keys = ['hourly_rate', 'salary', 'wage', 'labor_cost', 'actual_labor_cost']
    
    if 'evidence' in insight and isinstance(insight['evidence'], dict):
        for key in wage_keys:
            if key in insight['evidence']:
                insight['evidence'][key] = '***'
    
    return insight


def filter_insights_for_user(insights):
    """Filtruj seznam insightů podle role aktuálního uživatele"""
    role, user_id = get_current_user_role()
    
    if not role:
        return []
    
    filtered = []
    for insight in insights:
        filtered_insight = filter_insight_for_role(insight, role, user_id)
        if filtered_insight:
            filtered.append(filtered_insight)
    
    return filtered


# =============================================================================
# NOTIFIKACE - IN-APP + DIGEST
# =============================================================================

def apply_notification_migrations(db):
    """Vytvoř tabulky pro notifikace"""
    
    # Tabulka notifikací
    db.execute('''
        CREATE TABLE IF NOT EXISTS ai_notifications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            org_id INTEGER DEFAULT 1,
            user_id INTEGER NOT NULL,
            insight_id INTEGER,
            type TEXT NOT NULL,
            title TEXT NOT NULL,
            message TEXT,
            severity TEXT DEFAULT 'INFO',
            read_at TEXT,
            created_at TEXT DEFAULT (datetime('now')),
            FOREIGN KEY (insight_id) REFERENCES insight(id),
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    ''')
    
    # Index pro rychlé vyhledávání
    db.execute('CREATE INDEX IF NOT EXISTS idx_ai_notif_user ON ai_notifications(user_id, read_at)')
    db.execute('CREATE INDEX IF NOT EXISTS idx_ai_notif_created ON ai_notifications(created_at)')
    
    # Tabulka digest nastavení
    db.execute('''
        CREATE TABLE IF NOT EXISTS ai_notification_settings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER UNIQUE NOT NULL,
            digest_enabled INTEGER DEFAULT 1,
            digest_time TEXT DEFAULT '07:00',
            instant_critical INTEGER DEFAULT 1,
            email_enabled INTEGER DEFAULT 0,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    ''')
    
    # Tabulka digest historie
    db.execute('''
        CREATE TABLE IF NOT EXISTS ai_digest_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            digest_type TEXT NOT NULL,
            insights_count INTEGER DEFAULT 0,
            sent_at TEXT DEFAULT (datetime('now')),
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    ''')
    
    db.commit()
    print("✅ AI Notification tables created")


def create_notification_for_insight(insight, target_users=None):
    """
    Vytvoř notifikace pro insight.
    Pokud target_users je None, notifikuje podle pravidel relevance.
    """
    db = get_db_with_row_factory()
    
    insight_id = insight.get('id')
    insight_type = insight.get('type', '')
    severity = insight.get('severity', 'INFO')
    title = insight.get('title', '')
    summary = insight.get('summary', '')
    entity_type = insight.get('entity_type')
    entity_id = insight.get('entity_id')
    
    # Pokud nejsou specifikováni uživatelé, najdi relevantní
    if target_users is None:
        target_users = get_relevant_users_for_insight(insight)
    
    notifications_created = 0
    
    for user_id in target_users:
        # Zkontroluj roli uživatele
        user = db.execute('SELECT role FROM users WHERE id = ?', (user_id,)).fetchone()
        if not user:
            continue
        
        role = user['role'] or 'owner'
        
        # Zkontroluj jestli má vidět tento typ insightu
        if filter_insight_for_role(insight, role, user_id) is None:
            continue
        
        # Vytvoř notifikaci
        db.execute('''
            INSERT INTO ai_notifications (user_id, insight_id, type, title, message, severity)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (user_id, insight_id, insight_type, title, summary, severity))
        
        notifications_created += 1
    
    db.commit()
    return notifications_created


def get_relevant_users_for_insight(insight):
    """
    Najdi uživatele relevantní pro daný insight podle pravidel v PRD.
    """
    db = get_db_with_row_factory()
    
    insight_type = insight.get('type', '')
    severity = insight.get('severity', 'INFO')
    entity_type = insight.get('entity_type')
    entity_id = insight.get('entity_id')
    
    relevant_users = set()
    
    # KRITICKÉ insighty - všichni owner/admin
    if severity == 'CRITICAL':
        owners = db.execute("SELECT id FROM users WHERE role IN ('owner', 'admin') AND active = 1").fetchall()
        relevant_users.update(u['id'] for u in owners)
    
    # Finanční insighty - pouze owner/admin
    if insight_type in FINANCIAL_INSIGHT_TYPES:
        owners = db.execute("SELECT id FROM users WHERE role IN ('owner', 'admin') AND active = 1").fetchall()
        relevant_users.update(u['id'] for u in owners)
        return list(relevant_users)
    
    # Employee insighty - notifikuj samotného zaměstnance + jeho managera
    if entity_type == 'employee' and entity_id:
        relevant_users.add(entity_id)
        
        # Najdi managera
        emp = db.execute('SELECT manager_id FROM employees WHERE id = ?', (entity_id,)).fetchone()
        if emp and emp['manager_id']:
            relevant_users.add(emp['manager_id'])
    
    # Job insighty - notifikuj project managera a přiřazené lidi
    if entity_type == 'job' and entity_id:
        job = db.execute('SELECT project_manager_id FROM jobs WHERE id = ?', (entity_id,)).fetchone()
        if job and job['project_manager_id']:
            relevant_users.add(job['project_manager_id'])
        
        # Přiřazení zaměstnanci (pro WARN a výš)
        if severity in ('WARN', 'CRITICAL'):
            assigned = db.execute('SELECT employee_id FROM job_employees WHERE job_id = ?', (entity_id,)).fetchall()
            relevant_users.update(a['employee_id'] for a in assigned if a['employee_id'])
    
    # Task insighty - notifikuj přiřazeného
    if entity_type == 'task' and entity_id:
        task = db.execute('SELECT employee_id FROM tasks WHERE id = ?', (entity_id,)).fetchone()
        if task and task['employee_id']:
            relevant_users.add(task['employee_id'])
    
    # Warehouse insighty - notifikuj všechny managery
    if entity_type == 'warehouse_item':
        managers = db.execute("SELECT id FROM users WHERE role IN ('owner', 'admin', 'manager') AND active = 1").fetchall()
        relevant_users.update(m['id'] for m in managers)
    
    return list(relevant_users)


def get_user_notifications(user_id, unread_only=False, limit=50):
    """Získej notifikace pro uživatele"""
    db = get_db_with_row_factory()
    
    query = 'SELECT * FROM ai_notifications WHERE user_id = ?'
    params = [user_id]
    
    if unread_only:
        query += ' AND read_at IS NULL'
    
    query += ' ORDER BY created_at DESC LIMIT ?'
    params.append(limit)
    
    notifications = db.execute(query, params).fetchall()
    return [dict(n) for n in notifications]


def mark_notification_read(notification_id, user_id):
    """Označ notifikaci jako přečtenou"""
    db = get_db_with_row_factory()
    
    db.execute('''
        UPDATE ai_notifications 
        SET read_at = datetime('now')
        WHERE id = ? AND user_id = ?
    ''', (notification_id, user_id))
    db.commit()


def mark_all_notifications_read(user_id):
    """Označ všechny notifikace jako přečtené"""
    db = get_db_with_row_factory()
    
    db.execute('''
        UPDATE ai_notifications 
        SET read_at = datetime('now')
        WHERE user_id = ? AND read_at IS NULL
    ''', (user_id,))
    db.commit()


def get_unread_count(user_id):
    """Počet nepřečtených notifikací"""
    db = get_db_with_row_factory()
    
    result = db.execute('''
        SELECT COUNT(*) as count FROM ai_notifications 
        WHERE user_id = ? AND read_at IS NULL
    ''', (user_id,)).fetchone()
    
    return result['count'] if result else 0


# =============================================================================
# DIGEST GENERATION
# =============================================================================

def generate_morning_digest(user_id):
    """
    Vygeneruj ranní digest pro uživatele.
    Top 3 kritické + plán dne.
    """
    db = get_db_with_row_factory()
    
    # Získej roli pro filtrování
    user = db.execute('SELECT role FROM users WHERE id = ?', (user_id,)).fetchone()
    if not user:
        return None
    
    role = user['role'] or 'owner'
    
    # Top 3 kritické/warn insighty
    insights = db.execute('''
        SELECT * FROM insight
        WHERE status = 'open'
        ORDER BY 
            CASE severity WHEN 'CRITICAL' THEN 0 WHEN 'WARN' THEN 1 ELSE 2 END,
            created_at DESC
        LIMIT 10
    ''').fetchall()
    
    # Filtruj podle role
    filtered = []
    for i in insights:
        insight_dict = dict(i)
        if filter_insight_for_role(insight_dict, role, user_id):
            filtered.append(insight_dict)
        if len(filtered) >= 3:
            break
    
    # Plán dne - zakázky a úkoly
    today = datetime.now().date().isoformat()
    
    todays_jobs = db.execute('''
        SELECT j.id, j.client, j.name
        FROM jobs j
        JOIN job_employees je ON je.job_id = j.id
        WHERE je.employee_id = ?
        AND j.status IN ('active', 'Aktivní', 'rozpracováno')
        AND (j.start_date = ? OR j.planned_start_date = ?)
        LIMIT 5
    ''', (user_id, today, today)).fetchall()
    
    todays_tasks = db.execute('''
        SELECT id, title, due_date
        FROM tasks
        WHERE employee_id = ?
        AND status NOT IN ('done', 'completed', 'cancelled')
        AND due_date = ?
        LIMIT 5
    ''', (user_id, today)).fetchall()
    
    return {
        'type': 'morning_digest',
        'user_id': user_id,
        'date': today,
        'top_insights': filtered,
        'todays_jobs': [dict(j) for j in todays_jobs],
        'todays_tasks': [dict(t) for t in todays_tasks],
        'generated_at': datetime.now().isoformat()
    }


def generate_evening_digest(user_id):
    """
    Vygeneruj večerní digest - rizika na zítra.
    Počasí, chybějící materiál, nedokončené úkoly.
    """
    db = get_db_with_row_factory()
    
    tomorrow = (datetime.now().date() + timedelta(days=1)).isoformat()
    
    # Počasí rizika
    weather_risks = db.execute('''
        SELECT * FROM insight
        WHERE type = 'WEATHER_RISK_OUTDOOR'
        AND status = 'open'
        AND json_extract(evidence_json, '$.date') = ?
    ''', (tomorrow,)).fetchall()
    
    # Chybějící materiál
    material_risks = db.execute('''
        SELECT * FROM insight
        WHERE type IN ('LOW_STOCK', 'RESERVATION_EXCEEDS_STOCK')
        AND status = 'open'
        LIMIT 5
    ''').fetchall()
    
    # Zítřejší úkoly
    tomorrow_tasks = db.execute('''
        SELECT id, title, due_date
        FROM tasks
        WHERE employee_id = ?
        AND status NOT IN ('done', 'completed', 'cancelled')
        AND due_date = ?
    ''', (user_id, tomorrow)).fetchall()
    
    return {
        'type': 'evening_digest',
        'user_id': user_id,
        'date': tomorrow,
        'weather_risks': [dict(w) for w in weather_risks],
        'material_risks': [dict(m) for m in material_risks],
        'tomorrow_tasks': [dict(t) for t in tomorrow_tasks],
        'generated_at': datetime.now().isoformat()
    }


def log_digest_sent(user_id, digest_type, insights_count):
    """Zaloguj odeslání digestu"""
    db = get_db_with_row_factory()
    
    db.execute('''
        INSERT INTO ai_digest_log (user_id, digest_type, insights_count)
        VALUES (?, ?, ?)
    ''', (user_id, digest_type, insights_count))
    db.commit()


# =============================================================================
# FLASK API ROUTES
# =============================================================================

def register_notification_routes(app):
    """Registruj API routes pro notifikace"""
    
    @app.route('/api/ai/notifications')
    def api_get_notifications():
        """Seznam notifikací pro aktuálního uživatele"""
        uid = session.get('uid')
        if not uid:
            return jsonify({'error': 'unauthorized'}), 401
        
        unread_only = request.args.get('unread') == '1'
        limit = int(request.args.get('limit', 50))
        
        notifications = get_user_notifications(uid, unread_only, limit)
        unread_count = get_unread_count(uid)
        
        return jsonify({
            'notifications': notifications,
            'unread_count': unread_count,
            'total': len(notifications)
        })
    
    @app.route('/api/ai/notifications/unread-count')
    def api_unread_count():
        """Počet nepřečtených notifikací"""
        uid = session.get('uid')
        if not uid:
            return jsonify({'count': 0})
        
        return jsonify({'count': get_unread_count(uid)})
    
    @app.route('/api/ai/notifications/<int:notif_id>/read', methods=['POST'])
    def api_mark_read(notif_id):
        """Označ notifikaci jako přečtenou"""
        uid = session.get('uid')
        if not uid:
            return jsonify({'error': 'unauthorized'}), 401
        
        mark_notification_read(notif_id, uid)
        return jsonify({'success': True})
    
    @app.route('/api/ai/notifications/read-all', methods=['POST'])
    def api_mark_all_read():
        """Označ všechny notifikace jako přečtené"""
        uid = session.get('uid')
        if not uid:
            return jsonify({'error': 'unauthorized'}), 401
        
        mark_all_notifications_read(uid)
        return jsonify({'success': True})
    
    @app.route('/api/ai/digest/morning')
    def api_morning_digest():
        """Ranní digest pro aktuálního uživatele"""
        uid = session.get('uid')
        if not uid:
            return jsonify({'error': 'unauthorized'}), 401
        
        digest = generate_morning_digest(uid)
        return jsonify(digest)
    
    @app.route('/api/ai/digest/evening')
    def api_evening_digest():
        """Večerní digest pro aktuálního uživatele"""
        uid = session.get('uid')
        if not uid:
            return jsonify({'error': 'unauthorized'}), 401
        
        digest = generate_evening_digest(uid)
        return jsonify(digest)
    
    @app.route('/api/ai/notification-settings', methods=['GET', 'POST'])
    def api_notification_settings():
        """Nastavení notifikací"""
        uid = session.get('uid')
        if not uid:
            return jsonify({'error': 'unauthorized'}), 401
        
        db = get_db_with_row_factory()
        
        if request.method == 'GET':
            settings = db.execute(
                'SELECT * FROM ai_notification_settings WHERE user_id = ?', (uid,)
            ).fetchone()
            
            if not settings:
                # Výchozí nastavení
                return jsonify({
                    'digest_enabled': True,
                    'digest_time': '07:00',
                    'instant_critical': True,
                    'email_enabled': False
                })
            
            return jsonify(dict(settings))
        
        else:  # POST
            data = request.get_json() or {}
            
            db.execute('''
                INSERT INTO ai_notification_settings 
                    (user_id, digest_enabled, digest_time, instant_critical, email_enabled)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(user_id) DO UPDATE SET
                    digest_enabled = excluded.digest_enabled,
                    digest_time = excluded.digest_time,
                    instant_critical = excluded.instant_critical,
                    email_enabled = excluded.email_enabled
            ''', (
                uid,
                data.get('digest_enabled', 1),
                data.get('digest_time', '07:00'),
                data.get('instant_critical', 1),
                data.get('email_enabled', 0)
            ))
            db.commit()
            
            return jsonify({'success': True})
    
    print("✅ AI Notification routes registered")


# =============================================================================
# INTEGRATION HELPERS
# =============================================================================

def wrap_insights_api_with_rbac(original_get_insights_func):
    """
    Wrapper pro existující get_insights funkci který přidá RBAC filtrování.
    """
    def wrapped(*args, **kwargs):
        insights = original_get_insights_func(*args, **kwargs)
        return filter_insights_for_user(insights)
    return wrapped


def notify_on_new_insight(insight):
    """
    Callback pro volání při vytvoření nového insightu.
    Automaticky vytvoří notifikace pro relevantní uživatele.
    """
    severity = insight.get('severity', 'INFO')
    
    # Okamžitá notifikace pro CRITICAL
    if severity == 'CRITICAL':
        create_notification_for_insight(insight)
    
    # Pro ostatní se notifikace posílají v digestu
    elif severity == 'WARN':
        # Volitelně notifikovat i WARN
        db = get_db_with_row_factory()
        
        # Najdi uživatele s instant_critical = 1 (rozšířeno na WARN)
        users = db.execute('''
            SELECT user_id FROM ai_notification_settings 
            WHERE instant_critical = 1
        ''').fetchall()
        
        if users:
            create_notification_for_insight(insight, [u['user_id'] for u in users])
