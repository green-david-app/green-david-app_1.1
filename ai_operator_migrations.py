"""
GREEN DAVID APP - AI OPERÁTOR DATABÁZOVÉ MIGRACE
=================================================
Vytvoří tabulky: insight, action_draft, event_log
Podle PRD specifikace.
"""

def apply_ai_operator_migrations(db):
    """Aplikuj všechny migrace pro AI Operátor"""
    
    # 1. EVENT LOG - auditní páteř
    db.execute('''
        CREATE TABLE IF NOT EXISTS event_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            org_id INTEGER DEFAULT 1,
            actor_id INTEGER,
            actor_type TEXT DEFAULT 'user',
            entity_type TEXT NOT NULL,
            entity_id INTEGER,
            event_type TEXT NOT NULL,
            payload_json TEXT,
            created_at TEXT DEFAULT (datetime('now'))
        )
    ''')
    
    # Index pro rychlé vyhledávání
    db.execute('CREATE INDEX IF NOT EXISTS idx_event_log_entity ON event_log(entity_type, entity_id)')
    db.execute('CREATE INDEX IF NOT EXISTS idx_event_log_created ON event_log(created_at)')
    
    # 2. INSIGHT - signály a varování
    db.execute('''
        CREATE TABLE IF NOT EXISTS insight (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            org_id INTEGER DEFAULT 1,
            insight_key TEXT UNIQUE,
            type TEXT NOT NULL,
            severity TEXT DEFAULT 'INFO',
            status TEXT DEFAULT 'open',
            title TEXT NOT NULL,
            summary TEXT,
            evidence_json TEXT,
            actions_json TEXT,
            confidence TEXT DEFAULT 'HIGH',
            entity_type TEXT,
            entity_id INTEGER,
            created_at TEXT DEFAULT (datetime('now')),
            updated_at TEXT DEFAULT (datetime('now')),
            resolved_at TEXT,
            snoozed_until TEXT,
            dismissed_reason TEXT,
            dismissed_by INTEGER
        )
    ''')
    
    # Indexy pro insighty
    db.execute('CREATE INDEX IF NOT EXISTS idx_insight_status ON insight(status)')
    db.execute('CREATE INDEX IF NOT EXISTS idx_insight_severity ON insight(severity)')
    db.execute('CREATE INDEX IF NOT EXISTS idx_insight_type ON insight(type)')
    db.execute('CREATE INDEX IF NOT EXISTS idx_insight_entity ON insight(entity_type, entity_id)')
    
    # 3. ACTION DRAFT - návrhy akcí ke schválení
    db.execute('''
        CREATE TABLE IF NOT EXISTS action_draft (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            org_id INTEGER DEFAULT 1,
            insight_id INTEGER,
            created_by INTEGER,
            action_type TEXT NOT NULL,
            title TEXT,
            description TEXT,
            payload_json TEXT,
            status TEXT DEFAULT 'proposed',
            created_at TEXT DEFAULT (datetime('now')),
            approved_by INTEGER,
            approved_at TEXT,
            rejected_by INTEGER,
            rejected_at TEXT,
            rejection_reason TEXT,
            executed_at TEXT,
            execution_result_json TEXT,
            FOREIGN KEY (insight_id) REFERENCES insight(id)
        )
    ''')
    
    # Index pro action drafty
    db.execute('CREATE INDEX IF NOT EXISTS idx_action_draft_status ON action_draft(status)')
    db.execute('CREATE INDEX IF NOT EXISTS idx_action_draft_insight ON action_draft(insight_id)')
    
    # 4. Přidej sloupce do jobs pokud chybí (pro lepší tracking)
    try:
        db.execute('ALTER TABLE jobs ADD COLUMN budget_labor DECIMAL(12,2) DEFAULT 0')
    except:
        pass
    
    try:
        db.execute('ALTER TABLE jobs ADD COLUMN budget_materials DECIMAL(12,2) DEFAULT 0')
    except:
        pass
    
    try:
        db.execute('ALTER TABLE jobs ADD COLUMN actual_labor_cost DECIMAL(12,2) DEFAULT 0')
    except:
        pass
    
    try:
        db.execute('ALTER TABLE jobs ADD COLUMN actual_material_cost DECIMAL(12,2) DEFAULT 0')
    except:
        pass
    
    db.commit()
    print("✅ AI Operátor migrations applied (insight, action_draft, event_log)")


def log_event(db, entity_type, entity_id, event_type, payload=None, actor_id=None):
    """Zaloguj událost do event_log"""
    import json
    db.execute('''
        INSERT INTO event_log (actor_id, entity_type, entity_id, event_type, payload_json)
        VALUES (?, ?, ?, ?, ?)
    ''', (actor_id, entity_type, entity_id, event_type, json.dumps(payload) if payload else None))
    db.commit()
