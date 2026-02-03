"""
AI OPERATOR TABLES MIGRATION
=============================
Vytvoří tabulky pro Draft Actions systém a Insight States.

Spuštění:
  python ai_operator_tables_migration.py
"""

import sqlite3
import os

DB_PATH = 'app.db'

def migrate():
    """Provede migraci databáze"""
    
    if not os.path.exists(DB_PATH):
        print(f"❌ Databáze {DB_PATH} nenalezena")
        return False
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    print("🔧 AI Operator Tables Migration")
    print("=" * 50)
    
    # 1. Tabulka pro Draft Actions
    print("\n📋 Vytvářím tabulku ai_action_drafts...")
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS ai_action_drafts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            insight_id TEXT,
            type TEXT NOT NULL DEFAULT 'review',
            title TEXT NOT NULL,
            description TEXT,
            entity TEXT,
            entity_id INTEGER,
            payload TEXT,
            status TEXT NOT NULL DEFAULT 'pending',
            created_at TEXT NOT NULL,
            executed_at TEXT,
            executed_by INTEGER,
            result TEXT
        )
    ''')
    print("   ✅ ai_action_drafts vytvořena")
    
    # Index pro rychlé vyhledávání
    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_drafts_status ON ai_action_drafts(status)
    ''')
    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_drafts_entity ON ai_action_drafts(entity, entity_id)
    ''')
    
    # 2. Tabulka pro Insight States (snooze, dismiss)
    print("\n📋 Vytvářím tabulku ai_insight_states...")
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS ai_insight_states (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            insight_id TEXT NOT NULL UNIQUE,
            status TEXT NOT NULL DEFAULT 'active',
            snoozed_until TEXT,
            dismissed_reason TEXT,
            updated_at TEXT NOT NULL
        )
    ''')
    print("   ✅ ai_insight_states vytvořena")
    
    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_insight_states_id ON ai_insight_states(insight_id)
    ''')
    
    # 3. Tabulka pro Learning / Feedback (pro budoucí učení)
    print("\n📋 Vytvářím tabulku ai_learning_log...")
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS ai_learning_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            event_type TEXT NOT NULL,
            insight_id TEXT,
            draft_id INTEGER,
            action TEXT,
            outcome TEXT,
            user_id INTEGER,
            created_at TEXT NOT NULL,
            metadata TEXT
        )
    ''')
    print("   ✅ ai_learning_log vytvořena")
    
    # 4. Tabulka pro Event Log (pro offline sync)
    print("\n📋 Vytvářím tabulku ai_event_log...")
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS ai_event_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            event_type TEXT NOT NULL,
            entity_type TEXT,
            entity_id INTEGER,
            payload TEXT,
            source TEXT DEFAULT 'web',
            synced INTEGER DEFAULT 1,
            created_at TEXT NOT NULL,
            user_id INTEGER
        )
    ''')
    print("   ✅ ai_event_log vytvořena")
    
    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_event_log_synced ON ai_event_log(synced)
    ''')
    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_event_log_type ON ai_event_log(event_type)
    ''')
    
    # 5. Tabulka pro Company Preferences (nastavení firmy pro AI)
    print("\n📋 Vytvářím tabulku ai_company_preferences...")
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS ai_company_preferences (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            key TEXT NOT NULL UNIQUE,
            value TEXT,
            description TEXT,
            updated_at TEXT NOT NULL
        )
    ''')
    print("   ✅ ai_company_preferences vytvořena")
    
    # Vložení výchozích preferencí
    default_prefs = [
        ('max_weekly_hours', '45', 'Maximální pracovní hodiny týdně'),
        ('budget_warning_threshold', '90', 'Procento rozpočtu pro varování'),
        ('budget_critical_threshold', '110', 'Procento rozpočtu pro kritické varování'),
        ('inactive_days_warning', '5', 'Dny bez aktivity pro varování'),
        ('stock_warning_days', '7', 'Dny do vyčerpání skladu pro varování'),
        ('risk_tolerance', 'medium', 'Tolerance rizika (low/medium/high)'),
        ('auto_suggest_actions', '1', 'Automaticky navrhovat akce'),
        ('weather_check_enabled', '1', 'Kontrolovat počasí pro outdoor zakázky')
    ]
    
    for key, value, desc in default_prefs:
        cursor.execute('''
            INSERT OR IGNORE INTO ai_company_preferences (key, value, description, updated_at)
            VALUES (?, ?, ?, datetime('now'))
        ''', (key, value, desc))
    
    print("   ✅ Výchozí preference vloženy")
    
    conn.commit()
    conn.close()
    
    print("\n" + "=" * 50)
    print("✅ MIGRACE DOKONČENA")
    print("\nVytvořené tabulky:")
    print("  - ai_action_drafts (draft akce k potvrzení)")
    print("  - ai_insight_states (stav insightů - snooze/dismiss)")
    print("  - ai_learning_log (učení z rozhodnutí)")
    print("  - ai_event_log (event sourcing pro offline)")
    print("  - ai_company_preferences (nastavení AI)")
    
    return True


if __name__ == '__main__':
    migrate()
