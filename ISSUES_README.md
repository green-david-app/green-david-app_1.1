# Issues - Kompletní implementace ✅

## Co bylo implementováno:

### 1. Databáze
- ✅ Nová tabulka `issues` s těmito poli:
  - id, job_id, title, description
  - type (blocker/todo/note)
  - status (open/in_progress/resolved)
  - severity (critical/high/medium/low)
  - assigned_to (employee_id)
  - created_by, timestamps

### 2. Backend API (`main.py`)
- ✅ `/api/issues` - GET/POST/PATCH/DELETE
  - GET - filtr podle job_id, assigned_to, status
  - POST - vytvoření nového issue
  - PATCH - aktualizace (včetně auto-nastavení resolved_at)
  - DELETE - smazání issue
- ✅ Route `/issues` → issues.html

### 3. Frontend - Samostatná stránka Issues
- ✅ `/issues` (`issues.html`)
  - Dashboard se statistikami (blokující, řeší se, vyřešené)
  - Sekce "Přiřazené mně" - filtrované pro aktuálního uživatele
  - Sekce "Všechny issues"
  - Filtry podle statusu a typu
  - Tlačítko "Vyřešit" přímo na kartě

### 4. Integrace do Zakázek (`jobs.html`)
- ✅ Změna názvu z "Problémy / překážky" na "Issues"
- ✅ Propojení s API přes `jobs-issues.js`
  - addProblem() → POST /api/issues
  - resolveProblem() → PATCH /api/issues
  - deleteProblem() → DELETE /api/issues
  - Automatické načítání issues z API při renderOperativa()

### 5. Integrace do Úkolů (`tasks.html`)
- ✅ Nová sekce "Moje Issues" na začátku stránky
- ✅ Zobrazení počtu přiřazených issues
- ✅ Tlačítko "Zobrazit Issues" → přesměrování na /issues
- ✅ Tlačítko "Vyřešit" přímo u každého issue

### 6. Navigace
- ✅ Přidán link "🚨 issues" do bottom navigace (Více menu)

## JAK TO SPUSTIT:

### 1. Zastav aplikaci (pokud běží):
```bash
# V terminálu kde běží server: CTRL+C
```

### 2. Spusť SQL migraci:
```bash
cd /Users/greendavid/Desktop/green-david-WORK

# Spusť migraci pro vytvoření issues tabulky
python3 << 'EOF'
import sqlite3
db = sqlite3.connect('app.db')
with open('migrations/2026-01-04_create_issues.sql', 'r') as f:
    db.executescript(f.read())
db.commit()
print("✓ Issues tabulka vytvořena")
db.close()
EOF
```

### 3. Spusť aplikaci:
```bash
python3 main.py
```

### 4. Otevři v prohlížeči:
```
http://127.0.0.1:5000
```

## POUŽITÍ:

### Vytvoření issue u zakázky:
1. Jdi na detail zakázky
2. V sekci "Issues" vyplň:
   - Název issue
   - Typ (Blokuje/Kritické/Info)
   - Řeší (volitelné - delegovat na zaměstnance)
   - Poznámka (volitelné)
3. Klikni "+ Nahlásit"

### Zobrazení všech issues:
1. V navigaci → Více → 🚨 issues
2. Nebo přímo: http://127.0.0.1:5000/issues

### Zobrazení mých issues:
1. Sekce Úkoly → nahoře jsou "Moje Issues"
2. Nebo /issues → sekce "Přiřazené mně"

### Vyřešení issue:
- Klikni "Vyřešit" u konkrétního issue
- Automaticky se nastaví status "resolved" a čas vyřešení

## FLOW:

```
Zakázka → vytvoř Issue → přiřadím zaměstnanci
                        ↓
            Zaměstnanec se přihlásí
                        ↓
            Vidí v "Úkoly" sekci "Moje Issues"
                        ↓
            Klikne na issue → přesměruje na zakázku
                        ↓
            Vyřeší a označí "Vyřešit"
```

## SOUBORY KTERÉ BYLY ZMĚNĚNY/VYTVOŘENY:

### Nové soubory:
- `migrations/2026-01-04_create_issues.sql` - SQL migrace
- `issues.html` - Samostatná stránka pro issues
- `static/js/jobs-issues.js` - Propojení jobs s Issues API

### Upravené soubory:
- `main.py` - přidán /api/issues endpoint a route
- `jobs.html` - změna textu + import jobs-issues.js
- `tasks.html` - přidána sekce "Moje Issues"
- `static/bottom-nav.js` - přidán link na Issues

## POZNÁMKY:

- Issues jsou uložené v databázi (ne jako JSON)
- Propojené s zakázkami (job_id)
- Delegovatelné na zaměstnance (assigned_to)
- Status: open → in_progress → resolved
- Type: blocker (červená), todo (oranžová), note (modrá)
