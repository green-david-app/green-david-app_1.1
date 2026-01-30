# 🚀 Planning Module - Instalace a Nasazení

## Co tenhle modul dělá?

**Planning Module** přidává do Green David App kompletní systém plánování:

✅ **Multi-project Timeline** - vidíš všechny projekty v časové ose  
✅ **Daily Command Center** - ranní přehled co dnes musíš udělat  
✅ **Resource Management** - přiřazování lidí na projekty/dny  
✅ **Action Items** - kritické úkoly s deadliny (materiál, inspekce, subdodavatelé...)  
✅ **Material Logistics** - plánování dopravy materiálu  
✅ **Real-time Costs** - kolik už projekt stál  
✅ **Conflict Detection** - upozornění na kolize v plánování  
✅ **Personal Dashboards** - každý zaměstnanec vidí svůj plán  

---

## 📋 Krok za krokem instalace

### KROK 1: Záloha databáze

```bash
# VŽDYCKY si udělej zálohu před migrací!
cp app.db app.db.backup_before_planning
```

### KROK 2: Spusť migraci

```bash
python3 run_planning_migration.py
```

Co to udělá:
- Přidá nové sloupce do tabulek `tasks` a `jobs`
- Vytvoří nové tabulky: `action_items`, `material_deliveries`, `daily_plans`, `employee_groups`, `planning_conflicts`
- Vytvoří indexy pro rychlé vyhledávání
- Vytvoří view `v_today_overview` pro rychlý přehled

**Výstup by měl být:**
```
[Migration] Connecting to: app.db
[Backup] Created: app.db.backup_planning_user
[Migration] Reading: migrations/001_planning_module.sql
[Migration] Applying changes...
[Migration] ✅ SUCCESS - Planning module installed!
[Verify] New tables created: action_items, material_deliveries, daily_plans, employee_groups
```

### KROK 3: Restart aplikace

```bash
# Lokální vývoj
python3 main.py

# Nebo na Renderu
# Jen commitni změny a push do GitHub - Render restartuje automaticky
```

### KROK 4: Otestuj že to funguje

1. Otevři aplikaci v browseru
2. Jdi na: `http://localhost:5000/planning/daily`
3. Měl bys vidět stránku "Plánování - Dnes"

---

## 🎯 Co máš teď k dispozici

### Frontend stránky:
- `/planning/daily` - **Daily Command Center** (HOTOVÉ) ✅
- `/planning/timeline` - Multi-project Gantt view (TODO)
- `/planning/week` - Týdenní grid zaměstnanců (TODO)
- `/planning/costs` - Přehled nákladů (TODO)

### API endpointy:
- `GET /api/planning/timeline` - získá všechny projekty s úkoly
- `GET /api/planning/daily/<date>` - přehled daného dne
- `GET /api/planning/week` - týdenní plán
- `GET /api/planning/costs[/<job_id>]` - náklady projektů
- `POST /api/action-items` - vytvoř action item
- `GET /api/planning/actions/my` - moje action items
- `POST /api/material-delivery` - naplánuj dopravu
- `POST /api/planning/assign` - přiřaď člověka na den
- `GET /api/planning/employee/<id>` - personal dashboard

---

## 💡 Jak to používat

### 1. Daily Command Center (TEĎKA FUNKČNÍ)

**Navigace:**
```
http://localhost:5000/planning/daily
```

**Co vidíš:**
- Souhrn: kolik úkolů, akcí, dodávek dnes
- Konflikty (pokud jsou)
- Počasí (placeholder - později integrace)
- Seznam úkolů na dnes
- Action items co musíš vyřídit
- Dodávky materiálu
- Kdo kde pracuje

**Jak přidat data:**
- Klikni na "+"  buttony
- (Modaly zatím TODO - ale API funguje)

### 2. Přidání Action Item přes API

```javascript
fetch('/api/action-items', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({
        job_id: 1,
        title: 'Objednat dlažbu',
        description: 'Ceramic Pro 60x60',
        category: 'material',
        deadline: '2026-01-10',
        priority: 'high',
        notes: 'Objednat u Keramika Plus'
    })
})
```

### 3. Přiřazení zaměstnance na den

```javascript
fetch('/api/planning/assign', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({
        date: '2026-01-08',
        employee_id: 1,
        job_id: 3,
        hours_planned: 8,
        location: 'Příbram'
    })
})
```

### 4. Naplánování dodávky materiálu

```javascript
fetch('/api/material-delivery', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({
        job_id: 1,
        material_name: 'Cement 50kg',
        quantity: 20,
        unit: 'pytel',
        supplier: 'Stavebniny XY',
        delivery_date: '2026-01-09',
        delivery_time: 'morning',
        driver_id: 2,
        pickup_location: 'Stavebniny XY, Příbram',
        delivery_location: 'Stavba Centrum, Praha'
    })
})
```

---

## 🔧 Troubleshooting

### Problém: Migration failed

**Řešení:**
```bash
# Obnov zálohu
cp app.db.backup_before_planning app.db

# Zkus migraci znovu
python3 run_planning_migration.py
```

### Problém: "ModuleNotFoundError: No module named 'planning_api'"

**Řešení:**
Ujisti se, že máš tyto soubory v root složce projektu:
- `planning_api.py` ✅
- Import je přidán v `main.py` ✅

### Problém: Stránka /planning/daily ukazuje 404

**Řešení:**
1. Zkontroluj že soubor `planning-daily.html` existuje v root složce
2. Restart Flask serveru
3. Clear browser cache (Cmd+Shift+R na Macu)

### Problém: API vrací prázdná data

**Důvod:** Nemáš ještě žádná data v nových tabulkách

**Řešení:**
Přidej testovací data manuálně:
```sql
INSERT INTO action_items (job_id, title, category, deadline, priority, created_by)
VALUES (1, 'Test action', 'other', '2026-01-08', 'high', 1);
```

---

## 📊 Datový model - co bylo přidáno

### Nové sloupce v `tasks`:
- `planned_date` - kdy se má task dělat
- `planned_end_date` - kdy má být hotovo
- `estimated_hours` - odhad hodin
- `actual_cost` - kolik už to stálo
- `budget_hours` - rozpočet hodin

### Nová tabulka `action_items`:
Kritické úkoly co musíš vyřídit (ne "pracovat na", ale "zařídit"):
- Objednat materiál
- Inspekce
- Subdodavatel
- Dokumenty
- Klient

### Nová tabulka `material_deliveries`:
Plánování logistiky materiálu:
- Co se vozí
- Odkud / kam
- Kdo řídí
- Kdy

### Nová tabulka `daily_plans`:
Denní plány zaměstnanců:
- Kdo
- Kdy
- Na jaké zakázce
- Kolik hodin

### Nová tabulka `planning_conflicts`:
Automatická detekce kolizí:
- Zaměstnanec na 2 místech
- Materiál chybí
- Přetížení

---

## 🚀 Další kroky

### Fáze 1: DONE ✅
- [x] Databázová migrace
- [x] Backend API
- [x] Daily Command Center frontend

### Fáze 2: TODO (další kolo)
- [ ] Timeline view (multi-project Gantt)
- [ ] Weekly grid (kdo kde kdy)
- [ ] Modaly pro přidávání dat
- [ ] Mobile responsiveness
- [ ] Integrace s existujícími task modaly

### Fáze 3: Advanced features
- [ ] Drag & drop plánování
- [ ] Počasí API integrace
- [ ] AI predikce deadlinů
- [ ] Crew management
- [ ] Automatic conflict resolution

---

## 💬 Potřebuješ pomoc?

Pokud něco nefunguje nebo chceš pokračovat na dalších features:
1. Podívej se do logů: `tail -f nohup.out` (pokud používáš nohup)
2. Check browser console (F12)
3. Test API přes curl nebo Postman

**Test API:**
```bash
curl http://localhost:5000/api/planning/daily/2026-01-08
```

---

## 🎉 Hotovo!

Máš teď fungující základ Planning modulu.  
Otevři `/planning/daily` a začni plánovat! 🚀
