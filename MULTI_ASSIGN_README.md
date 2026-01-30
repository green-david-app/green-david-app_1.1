# Multi-Assign Update ✅

## CO JE NOVÉHO:

### 1. Více zaměstnanců na úkol/issue
- ✅ Můžeš přiřadit více lidí na jeden úkol nebo issue
- ✅ Každý přiřazený uvidí úkol/issue ve svém "To-Do"
- ✅ Hlavní odpovědný je označen hvězdičkou ★

### 2. Úkoly propojené s API
- ✅ "Úkoly (to-do)" ze zakázek se teď ukládají do databáze
- ✅ Automaticky se zobrazují v sekci "Úkoly"
- ✅ Stejný systém jako Issues

### 3. Nové databázové tabulky
- ✅ `task_assignments` - přiřazení zaměstnanců k úkolům
- ✅ `issue_assignments` - přiřazení zaměstnanců k issues

## JAK TO FUNGUJE:

### Vytvoření úkolu/issue s více lidmi:

```javascript
// Příklad API volání
POST /api/tasks
{
    "job_id": 123,
    "title": "Dokončit podklad",
    "assigned_employees": [5, 8, 12],  // IDs zaměstnanců
    "primary_employee": 5               // Hlavní odpovědný
}
```

### Zobrazení úkolů/issues přiřazeného zaměstnance:

```javascript
GET /api/tasks?employee_id=5
// Vrátí všechny úkoly kde je zaměstnanec 5 přiřazený
```

### Každý úkol/issue obsahuje:

```json
{
    "id": 123,
    "title": "Název úkolu",
    "assignees": [
        {"id": 5, "name": "Jan Novák", "is_primary": true},
        {"id": 8, "name": "Petr Svoboda", "is_primary": false}
    ]
}
```

## INSTALACE:

Tato verze je už **zabudovaná** v green-david-COMPLETE.zip!

Pokud aktualizuješ existující instalaci:

```bash
cd /Users/greendavid/Desktop/green-david-WORK

# 1. Zastav aplikaci (CTRL+C)

# 2. Vytvoř assignment tabulky
python3 << 'EOF'
import sqlite3
db = sqlite3.connect('app.db')
db.executescript('''
CREATE TABLE IF NOT EXISTS task_assignments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    task_id INTEGER NOT NULL,
    employee_id INTEGER NOT NULL,
    is_primary BOOLEAN DEFAULT 0,
    created_at TEXT DEFAULT (datetime('now')),
    FOREIGN KEY (task_id) REFERENCES tasks(id) ON DELETE CASCADE,
    FOREIGN KEY (employee_id) REFERENCES employees(id) ON DELETE CASCADE,
    UNIQUE(task_id, employee_id)
);

CREATE TABLE IF NOT EXISTS issue_assignments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    issue_id INTEGER NOT NULL,
    employee_id INTEGER NOT NULL,
    is_primary BOOLEAN DEFAULT 0,
    created_at TEXT DEFAULT (datetime('now')),
    FOREIGN KEY (issue_id) REFERENCES issues(id) ON DELETE CASCADE,
    FOREIGN KEY (employee_id) REFERENCES employees(id) ON DELETE CASCADE,
    UNIQUE(issue_id, employee_id)
);

CREATE INDEX IF NOT EXISTS idx_task_assignments_task ON task_assignments(task_id);
CREATE INDEX IF NOT EXISTS idx_task_assignments_employee ON task_assignments(employee_id);
CREATE INDEX IF NOT EXISTS idx_issue_assignments_issue ON issue_assignments(issue_id);
CREATE INDEX IF NOT EXISTS idx_issue_assignments_employee ON issue_assignments(employee_id);
''')
db.commit()
print('✓ Assignment tabulky vytvořeny')
db.close()
EOF

# 3. Nahraď soubory z nového ZIPu:
#    - main.py
#    - assignment_helpers.py (NOVÝ)
#    - jobs.html
#    - static/js/jobs-tasks.js (NOVÝ)
#    - static/js/multi-employee-selector.js (NOVÝ)

# 4. Spusť aplikaci
python3 main.py
```

## POUŽITÍ:

### V zakázkách:

1. **Issues sekce:**
   - Zadej název issue
   - Vyber typ (Blokuje/Kritické/Info)
   - **V budoucnu**: Klikni na "Řeší" → vybereš více lidí + primárního
   - Klikni "+ Nahlásit"

2. **Úkoly (to-do) sekce:**
   - Zadej název úkolu
   - **V budoucnu**: Vybereš více lidí + primárního
   - Klikni "+ Přidat"

### Co se stane:

1. Úkol/Issue se uloží do databáze
2. Zobrazí se v `/tasks` nebo `/issues`
3. Všichni přiřazení zaměstnanci ho uvidí ve svém "To-Do"
4. Hlavní odpovědný je označen hvězdičkou ★

## SOUBORY:

### Nové:
- `assignment_helpers.py` - Helper funkce pro multi-assign
- `static/js/jobs-tasks.js` - Propojení úkolů z jobs s API
- `static/js/multi-employee-selector.js` - UI komponenta (připraveno pro budoucnost)

### Upravené:
- `main.py` - API rozšířené o multi-assign
- `jobs.html` - import jobs-tasks.js
- `app.db` - nové tabulky task_assignments a issue_assignments

## TODO (pro budoucí verzi):

UI komponenta `MultiEmployeeSelector` je připravená, ale zatím není integrovaná do jobs.html.
Pro plnou funkčnost multi-select UI bude potřeba:
1. Přidat multi-employee-selector.js do jobs.html
2. Upravit formuláře pro issue/task aby používaly MultiEmployeeSelector komponentu
3. Poslat selected_employees místo jednoho assigned_to

**AKTUÁLNĚ**: Backend podporuje multi-assign, ale frontend zatím používá single-select.
