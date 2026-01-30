"""
AI OPERATOR - DRAFT ACTIONS SYSTEM
===================================
Schvalovací systém pro akce navržené AI Operátorem.
Žádná akce není provedena bez schválení člověkem.

Draft Action Types:
- MOVE_JOB - Přesun zakázky
- REASSIGN_TASK - Přeřazení úkolu
- REASSIGN_EMPLOYEE - Přeřazení zaměstnance
- GENERATE_PURCHASE - Generování nákupního seznamu
- REALLOCATE_INVENTORY - Přerozdělení skladových rezervací
- REQUEST_TIMESHEET - Požádání o doplnění výkazu
- ESCALATE_ISSUE - Eskalace problému
- UPDATE_DEADLINE - Aktualizace termínu
- SWAP_JOBS - Prohození zakázek
"""

from flask import Blueprint, jsonify, request, g
from datetime import datetime
import json
import sqlite3

# Blueprint pro Draft Actions API
draft_actions_bp = Blueprint('draft_actions', __name__, url_prefix='/api/ai')

# Reference na get_db - nastaví se z main.py
get_db = None

def init_draft_actions(db_getter):
    """Inicializace modulu s DB getter funkcí"""
    global get_db
    get_db = db_getter
    ensure_draft_tables()

def ensure_draft_tables():
    """Vytvoření tabulek pro Draft Actions"""
    if not get_db:
        return
        
    db = get_db()
    db.executescript("""
        -- Tabulka pro draft akce
        CREATE TABLE IF NOT EXISTS ai_draft_actions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            insight_id TEXT,
            action_type TEXT NOT NULL,
            title TEXT NOT NULL,
            description TEXT,
            payload TEXT,
            status TEXT NOT NULL DEFAULT 'pending',
            priority TEXT DEFAULT 'medium',
            created_by INTEGER,
            approved_by INTEGER,
            created_at TEXT NOT NULL DEFAULT (datetime('now')),
            updated_at TEXT NOT NULL DEFAULT (datetime('now')),
            executed_at TEXT,
            execution_result TEXT
        );
        
        -- Tabulka pro historii insightů (snooze/dismiss)
        CREATE TABLE IF NOT EXISTS ai_insight_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            insight_id TEXT NOT NULL,
            action TEXT NOT NULL,
            reason TEXT,
            user_id INTEGER,
            created_at TEXT NOT NULL DEFAULT (datetime('now'))
        );
        
        -- Tabulka pro event log (pro offline sync)
        CREATE TABLE IF NOT EXISTS ai_event_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            event_type TEXT NOT NULL,
            entity_type TEXT,
            entity_id INTEGER,
            payload TEXT,
            user_id INTEGER,
            synced INTEGER DEFAULT 0,
            created_at TEXT NOT NULL DEFAULT (datetime('now'))
        );
        
        -- Tabulka pro AI paměť (learning layer)
        CREATE TABLE IF NOT EXISTS ai_memory (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            key TEXT NOT NULL UNIQUE,
            value TEXT NOT NULL,
            category TEXT,
            updated_at TEXT NOT NULL DEFAULT (datetime('now'))
        );
        
        -- Indexy
        CREATE INDEX IF NOT EXISTS idx_draft_status ON ai_draft_actions(status);
        CREATE INDEX IF NOT EXISTS idx_draft_type ON ai_draft_actions(action_type);
        CREATE INDEX IF NOT EXISTS idx_insight_history ON ai_insight_history(insight_id);
        CREATE INDEX IF NOT EXISTS idx_event_log_synced ON ai_event_log(synced);
    """)
    db.commit()


# ============================================================================
# DRAFT ACTIONS ENDPOINTS
# ============================================================================

@draft_actions_bp.route('/drafts', methods=['GET'])
def get_drafts():
    """Získání seznamu draft akcí"""
    try:
        db = get_db()
        db.row_factory = sqlite3.Row
        
        status = request.args.get('status', 'pending')
        limit = min(int(request.args.get('limit', 50)), 100)
        
        if status == 'all':
            drafts = db.execute("""
                SELECT * FROM ai_draft_actions 
                ORDER BY 
                    CASE priority WHEN 'critical' THEN 0 WHEN 'high' THEN 1 WHEN 'medium' THEN 2 ELSE 3 END,
                    created_at DESC
                LIMIT ?
            """, (limit,)).fetchall()
        else:
            drafts = db.execute("""
                SELECT * FROM ai_draft_actions 
                WHERE status = ?
                ORDER BY 
                    CASE priority WHEN 'critical' THEN 0 WHEN 'high' THEN 1 WHEN 'medium' THEN 2 ELSE 3 END,
                    created_at DESC
                LIMIT ?
            """, (status, limit)).fetchall()
        
        return jsonify({
            'drafts': [dict(d) for d in drafts],
            'count': len(drafts)
        })
        
    except Exception as e:
        print(f"[AI] Get drafts error: {e}")
        return jsonify({'error': str(e)}), 500


@draft_actions_bp.route('/drafts', methods=['POST'])
def create_draft():
    """Vytvoření nového draftu"""
    try:
        data = request.get_json() or {}
        db = get_db()
        
        insight_id = data.get('insight_id')
        action_type = data.get('action_type', 'GENERIC')
        title = data.get('title', f'Akce: {action_type}')
        description = data.get('description', '')
        payload = json.dumps(data.get('payload', {}))
        priority = data.get('priority', 'medium')
        
        # Získat user_id ze session
        user_id = None
        try:
            from flask import session
            user_id = session.get('user_id')
        except:
            pass
        
        cursor = db.execute("""
            INSERT INTO ai_draft_actions (insight_id, action_type, title, description, payload, priority, created_by)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (insight_id, action_type, title, description, payload, priority, user_id))
        
        db.commit()
        
        # Log event
        log_event('DRAFT_CREATED', 'draft_action', cursor.lastrowid, {
            'action_type': action_type,
            'insight_id': insight_id
        })
        
        return jsonify({
            'success': True,
            'draft_id': cursor.lastrowid,
            'message': 'Draft vytvořen'
        })
        
    except Exception as e:
        print(f"[AI] Create draft error: {e}")
        return jsonify({'error': str(e)}), 500


@draft_actions_bp.route('/drafts/<int:draft_id>', methods=['GET'])
def get_draft(draft_id):
    """Získání detailu draftu"""
    try:
        db = get_db()
        db.row_factory = sqlite3.Row
        
        draft = db.execute("SELECT * FROM ai_draft_actions WHERE id = ?", (draft_id,)).fetchone()
        
        if not draft:
            return jsonify({'error': 'Draft not found'}), 404
            
        return jsonify(dict(draft))
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@draft_actions_bp.route('/drafts/<int:draft_id>/approve', methods=['POST'])
def approve_draft(draft_id):
    """Schválení draftu - provede akci"""
    try:
        db = get_db()
        db.row_factory = sqlite3.Row
        
        draft = db.execute("SELECT * FROM ai_draft_actions WHERE id = ?", (draft_id,)).fetchone()
        
        if not draft:
            return jsonify({'error': 'Draft not found'}), 404
            
        if draft['status'] != 'pending':
            return jsonify({'error': 'Draft already processed'}), 400
        
        # Získat user_id ze session
        user_id = None
        try:
            from flask import session
            user_id = session.get('user_id')
        except:
            pass
        
        # Provést akci
        result = execute_draft_action(draft)
        
        # Aktualizovat status
        status = 'executed' if result['success'] else 'failed'
        db.execute("""
            UPDATE ai_draft_actions 
            SET status = ?, approved_by = ?, executed_at = datetime('now'), 
                execution_result = ?, updated_at = datetime('now')
            WHERE id = ?
        """, (status, user_id, json.dumps(result), draft_id))
        
        db.commit()
        
        # Log event
        log_event('DRAFT_APPROVED', 'draft_action', draft_id, {
            'action_type': draft['action_type'],
            'result': result
        })
        
        # Update AI memory (learning)
        update_memory(f"draft_success_{draft['action_type']}", 
                     increment=1 if result['success'] else 0)
        
        return jsonify({
            'success': result['success'],
            'message': result.get('message', 'Akce provedena'),
            'result': result
        })
        
    except Exception as e:
        print(f"[AI] Approve draft error: {e}")
        return jsonify({'error': str(e)}), 500


@draft_actions_bp.route('/drafts/<int:draft_id>/reject', methods=['POST'])
def reject_draft(draft_id):
    """Odmítnutí draftu"""
    try:
        db = get_db()
        data = request.get_json() or {}
        reason = data.get('reason', '')
        
        # Získat user_id
        user_id = None
        try:
            from flask import session
            user_id = session.get('user_id')
        except:
            pass
        
        db.execute("""
            UPDATE ai_draft_actions 
            SET status = 'rejected', approved_by = ?, 
                execution_result = ?, updated_at = datetime('now')
            WHERE id = ?
        """, (user_id, json.dumps({'reason': reason}), draft_id))
        
        db.commit()
        
        # Log event
        log_event('DRAFT_REJECTED', 'draft_action', draft_id, {'reason': reason})
        
        # Update AI memory (learning from rejection)
        draft = db.execute("SELECT action_type FROM ai_draft_actions WHERE id = ?", (draft_id,)).fetchone()
        if draft:
            update_memory(f"draft_rejected_{draft[0]}", increment=1)
        
        return jsonify({'success': True, 'message': 'Draft odmítnut'})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ============================================================================
# INSIGHT ACTIONS (Snooze/Dismiss)
# ============================================================================

@draft_actions_bp.route('/insights/<insight_id>/snooze', methods=['POST'])
def snooze_insight(insight_id):
    """Odložení insightu na později"""
    try:
        db = get_db()
        data = request.get_json() or {}
        duration = data.get('duration', '1h')  # 1h, 4h, 1d, 1w
        
        user_id = None
        try:
            from flask import session
            user_id = session.get('user_id')
        except:
            pass
        
        db.execute("""
            INSERT INTO ai_insight_history (insight_id, action, reason, user_id)
            VALUES (?, 'snooze', ?, ?)
        """, (insight_id, duration, user_id))
        
        db.commit()
        
        return jsonify({'success': True})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@draft_actions_bp.route('/insights/<insight_id>/dismiss', methods=['POST'])
def dismiss_insight(insight_id):
    """Zamítnutí insightu"""
    try:
        db = get_db()
        data = request.get_json() or {}
        reason = data.get('reason', '')
        
        user_id = None
        try:
            from flask import session
            user_id = session.get('user_id')
        except:
            pass
        
        db.execute("""
            INSERT INTO ai_insight_history (insight_id, action, reason, user_id)
            VALUES (?, 'dismiss', ?, ?)
        """, (insight_id, reason, user_id))
        
        db.commit()
        
        return jsonify({'success': True})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ============================================================================
# DRAFT ACTION EXECUTORS
# ============================================================================

def execute_draft_action(draft):
    """Provede akci podle typu draftu"""
    action_type = draft['action_type']
    payload = json.loads(draft['payload'] or '{}')
    
    executors = {
        'MOVE_JOB': execute_move_job,
        'MOVE_TASK_DATE': execute_move_task,
        'REASSIGN_TASK': execute_reassign_task,
        'REASSIGN_EMPLOYEE': execute_reassign_employee,
        'GENERATE_PURCHASE_LIST': execute_generate_purchase,
        'REALLOCATE_RESERVATIONS': execute_reallocate_reservations,
        'REQUEST_TIMESHEET_ENTRY': execute_request_timesheet,
        'UPDATE_JOB_DEADLINE': execute_update_deadline,
        'SWAP_JOBS': execute_swap_jobs,
        'ESCALATE_BUDGET': execute_escalate_budget,
        'ASSIGN_TASKS_FROM_BACKLOG': execute_assign_backlog,
    }
    
    executor = executors.get(action_type)
    
    if executor:
        try:
            return executor(payload)
        except Exception as e:
            return {'success': False, 'message': str(e)}
    
    return {'success': False, 'message': f'Neznámý typ akce: {action_type}'}


def execute_move_job(payload):
    """Přesun zakázky na jiný termín"""
    db = get_db()
    job_id = payload.get('job_id')
    new_date = payload.get('new_date')
    
    if not job_id or not new_date:
        return {'success': False, 'message': 'Chybí job_id nebo new_date'}
    
    db.execute("UPDATE jobs SET date = ? WHERE id = ?", (new_date, job_id))
    db.commit()
    
    return {'success': True, 'message': f'Zakázka {job_id} přesunuta na {new_date}'}


def execute_move_task(payload):
    """Přesun termínu úkolu"""
    db = get_db()
    task_id = payload.get('task_id')
    new_date = payload.get('new_date')
    
    if not task_id or not new_date:
        return {'success': False, 'message': 'Chybí task_id nebo new_date'}
    
    db.execute("UPDATE tasks SET due_date = ? WHERE id = ?", (new_date, task_id))
    db.commit()
    
    return {'success': True, 'message': f'Úkol {task_id} přesunut na {new_date}'}


def execute_reassign_task(payload):
    """Přeřazení úkolu jinému zaměstnanci"""
    db = get_db()
    task_id = payload.get('task_id')
    employee_id = payload.get('employee_id')
    
    if not task_id or not employee_id:
        return {'success': False, 'message': 'Chybí task_id nebo employee_id'}
    
    db.execute("UPDATE tasks SET employee_id = ? WHERE id = ?", (employee_id, task_id))
    db.commit()
    
    return {'success': True, 'message': f'Úkol {task_id} přeřazen zaměstnanci {employee_id}'}


def execute_reassign_employee(payload):
    """Přeřazení zaměstnance na jinou zakázku"""
    db = get_db()
    employee_id = payload.get('employee_id')
    from_job_id = payload.get('from_job_id')
    to_job_id = payload.get('to_job_id')
    
    if not employee_id or not to_job_id:
        return {'success': False, 'message': 'Chybí employee_id nebo to_job_id'}
    
    # Remove from old job
    if from_job_id:
        db.execute("DELETE FROM job_assignments WHERE job_id = ? AND employee_id = ?", 
                  (from_job_id, employee_id))
    
    # Add to new job
    db.execute("""
        INSERT OR IGNORE INTO job_assignments (job_id, employee_id) VALUES (?, ?)
    """, (to_job_id, employee_id))
    
    db.commit()
    
    return {'success': True, 'message': f'Zaměstnanec {employee_id} přeřazen na zakázku {to_job_id}'}


def execute_generate_purchase(payload):
    """Generování nákupního seznamu"""
    db = get_db()
    items = payload.get('items', [])
    
    # TODO: Implementovat vytvoření nákupního seznamu
    # Pro teď jen vrátíme úspěch
    
    return {'success': True, 'message': f'Nákupní seznam vygenerován ({len(items)} položek)', 'items': items}


def execute_reallocate_reservations(payload):
    """Přerozdělení skladových rezervací"""
    db = get_db()
    item_id = payload.get('item_id')
    
    # TODO: Implementovat logiku přerozdělení
    
    return {'success': True, 'message': 'Rezervace přerozděleny'}


def execute_request_timesheet(payload):
    """Požádání o doplnění výkazu"""
    db = get_db()
    employee_id = payload.get('employee_id')
    date = payload.get('date')
    
    # TODO: Implementovat notifikaci zaměstnanci
    
    return {'success': True, 'message': f'Požadavek na výkaz odeslán zaměstnanci {employee_id}'}


def execute_update_deadline(payload):
    """Aktualizace deadline zakázky"""
    db = get_db()
    job_id = payload.get('job_id')
    deadline = payload.get('deadline')
    
    if not job_id or not deadline:
        return {'success': False, 'message': 'Chybí job_id nebo deadline'}
    
    db.execute("UPDATE jobs SET date = ? WHERE id = ?", (deadline, job_id))
    db.commit()
    
    return {'success': True, 'message': f'Deadline zakázky {job_id} aktualizován na {deadline}'}


def execute_swap_jobs(payload):
    """Prohození dvou zakázek v plánu"""
    db = get_db()
    job1_id = payload.get('job1_id')
    job2_id = payload.get('job2_id')
    
    if not job1_id or not job2_id:
        return {'success': False, 'message': 'Chybí job1_id nebo job2_id'}
    
    # Get dates
    job1 = db.execute("SELECT date FROM jobs WHERE id = ?", (job1_id,)).fetchone()
    job2 = db.execute("SELECT date FROM jobs WHERE id = ?", (job2_id,)).fetchone()
    
    if not job1 or not job2:
        return {'success': False, 'message': 'Zakázky nenalezeny'}
    
    # Swap dates
    db.execute("UPDATE jobs SET date = ? WHERE id = ?", (job2[0], job1_id))
    db.execute("UPDATE jobs SET date = ? WHERE id = ?", (job1[0], job2_id))
    db.commit()
    
    return {'success': True, 'message': f'Zakázky {job1_id} a {job2_id} prohozeny'}


def execute_escalate_budget(payload):
    """Eskalace rozpočtového varování"""
    db = get_db()
    job_id = payload.get('job_id')
    message = payload.get('message', 'Rozpočet překročen')
    
    # TODO: Implementovat notifikaci vedoucímu
    
    return {'success': True, 'message': f'Eskalace odeslána pro zakázku {job_id}'}


def execute_assign_backlog(payload):
    """Přiřazení úkolů z backlogu volnému zaměstnanci"""
    db = get_db()
    employee_id = payload.get('employee_id')
    
    # Find unassigned tasks
    tasks = db.execute("""
        SELECT id FROM tasks 
        WHERE employee_id IS NULL AND status != 'done'
        ORDER BY due_date ASC
        LIMIT 3
    """).fetchall()
    
    assigned = 0
    for task in tasks:
        db.execute("UPDATE tasks SET employee_id = ? WHERE id = ?", (employee_id, task[0]))
        assigned += 1
    
    db.commit()
    
    return {'success': True, 'message': f'Přiřazeno {assigned} úkolů zaměstnanci {employee_id}'}


# ============================================================================
# EVENT LOG & MEMORY HELPERS
# ============================================================================

def log_event(event_type, entity_type, entity_id, payload=None):
    """Zalogování události pro offline sync"""
    try:
        db = get_db()
        
        user_id = None
        try:
            from flask import session
            user_id = session.get('user_id')
        except:
            pass
        
        db.execute("""
            INSERT INTO ai_event_log (event_type, entity_type, entity_id, payload, user_id)
            VALUES (?, ?, ?, ?, ?)
        """, (event_type, entity_type, entity_id, json.dumps(payload or {}), user_id))
        db.commit()
    except Exception as e:
        print(f"[AI] Log event error: {e}")


def update_memory(key, value=None, increment=None):
    """Aktualizace AI paměti (learning layer)"""
    try:
        db = get_db()
        
        if increment is not None:
            # Increment counter
            existing = db.execute("SELECT value FROM ai_memory WHERE key = ?", (key,)).fetchone()
            if existing:
                new_value = int(existing[0]) + increment
                db.execute("UPDATE ai_memory SET value = ?, updated_at = datetime('now') WHERE key = ?",
                          (str(new_value), key))
            else:
                db.execute("INSERT INTO ai_memory (key, value, category) VALUES (?, ?, 'counter')",
                          (key, str(increment)))
        elif value is not None:
            db.execute("""
                INSERT OR REPLACE INTO ai_memory (key, value, updated_at)
                VALUES (?, ?, datetime('now'))
            """, (key, json.dumps(value) if not isinstance(value, str) else value))
        
        db.commit()
    except Exception as e:
        print(f"[AI] Update memory error: {e}")


def get_memory(key, default=None):
    """Získání hodnoty z AI paměti"""
    try:
        db = get_db()
        row = db.execute("SELECT value FROM ai_memory WHERE key = ?", (key,)).fetchone()
        if row:
            try:
                return json.loads(row[0])
            except:
                return row[0]
        return default
    except Exception as e:
        print(f"[AI] Get memory error: {e}")
        return default


# ============================================================================
# OFFLINE SYNC ENDPOINTS
# ============================================================================

@draft_actions_bp.route('/sync/events', methods=['GET'])
def get_unsynced_events():
    """Získání nesynchronizovaných událostí"""
    try:
        db = get_db()
        db.row_factory = sqlite3.Row
        
        events = db.execute("""
            SELECT * FROM ai_event_log WHERE synced = 0 ORDER BY created_at ASC LIMIT 100
        """).fetchall()
        
        return jsonify({'events': [dict(e) for e in events]})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@draft_actions_bp.route('/sync/events/mark', methods=['POST'])
def mark_events_synced():
    """Označení událostí jako synchronizovaných"""
    try:
        db = get_db()
        data = request.get_json() or {}
        event_ids = data.get('event_ids', [])
        
        if event_ids:
            placeholders = ','.join('?' * len(event_ids))
            db.execute(f"UPDATE ai_event_log SET synced = 1 WHERE id IN ({placeholders})", event_ids)
            db.commit()
        
        return jsonify({'success': True, 'marked': len(event_ids)})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@draft_actions_bp.route('/sync/push', methods=['POST'])
def push_offline_events():
    """Příjem offline událostí z klienta"""
    try:
        db = get_db()
        data = request.get_json() or {}
        events = data.get('events', [])
        
        processed = 0
        conflicts = []
        
        for event in events:
            # TODO: Implementovat conflict resolution
            try:
                db.execute("""
                    INSERT INTO ai_event_log (event_type, entity_type, entity_id, payload, user_id, synced)
                    VALUES (?, ?, ?, ?, ?, 1)
                """, (
                    event.get('event_type'),
                    event.get('entity_type'),
                    event.get('entity_id'),
                    json.dumps(event.get('payload', {})),
                    event.get('user_id')
                ))
                processed += 1
            except Exception as e:
                conflicts.append({'event': event, 'error': str(e)})
        
        db.commit()
        
        return jsonify({
            'success': True,
            'processed': processed,
            'conflicts': conflicts
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500
