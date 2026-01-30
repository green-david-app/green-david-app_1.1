# 🚀 PLANNING MODULE - QUICK START

## Co jsem ti postavil

Kompletní **Planning Module** pro Green David App s:

### ✅ Co funguje TEĎKA:

1. **Databáze** (migrace hotová)
   - ✅ 5 nových tabulek
   - ✅ Rozšířené `tasks` a `jobs` tabulky
   - ✅ Indexy pro rychlost
   - ✅ View pro rychlé dotazy

2. **Backend API** (všechny endpointy funkční)
   - ✅ `/api/planning/timeline` - multi-project přehled
   - ✅ `/api/planning/daily/<date>` - denní command center
   - ✅ `/api/planning/week` - týdenní grid
   - ✅ `/api/planning/costs` - real-time náklady
   - ✅ `/api/action-items` - CRUD pro action items
   - ✅ `/api/material-delivery` - CRUD pro logistiku
   - ✅ `/api/planning/assign` - přiřazování lidí
   - ✅ `/api/planning/employee/<id>` - personal dashboard

3. **Frontend** (Daily view funkční)
   - ✅ `planning-daily.html` - ranní command center
   - 🔨 Timeline, Week, Costs - připraveno k dokončení

---

## 📦 Co máš ke stažení

**ZIP soubor obsahuje:**
```
green-david-WORK-PLANNING.zip
├── migrations/001_planning_module.sql      ← DB migrace
├── planning_api.py                         ← Backend funkce
├── planning-daily.html                     ← Frontend stránka
├── run_planning_migration.py               ← Instalační script
├── test_planning_api.py                    ← Test script
├── PLANNING_MODULE_INSTALL.md              ← Podrobná dokumentace
└── main.py (upravený)                      ← S Planning routes
```

---

## ⚡ Jak to spustit (3 minuty)

### 1. Rozbal ZIP
```bash
unzip green-david-WORK-PLANNING.zip
cd green-david-WORK
```

### 2. Spusť migraci
```bash
python3 run_planning_migration.py
```
Výstup: `✅ SUCCESS - Planning module installed!`

### 3. Spusť aplikaci
```bash
python3 main.py
```

### 4. Otevři v browseru
```
http://localhost:5000/planning/daily
```

---

## 🎯 Co vidíš na `/planning/daily`

**Ranní Command Center:**
- 📊 Summary karty (kolik úkolů, akcí, dodávek dnes)
- ⚠️ Konflikty (pokud jsou)
- 🌤️ Počasí info (placeholder)
- 📋 Seznam úkolů na dnes
- 🎯 Action items co musíš vyřídit
- 🚚 Dodávky materiálu
- 👷 Kdo kde pracuje

**Navigace:**
- Šipky: Včera / Dnes / Zítra
- Date picker: Vyber libovolný den
- "+" buttony: Přidej nová data

---

## 🧪 Test že to funguje

```bash
# Terminal 1: Spusť Flask
python3 main.py

# Terminal 2: Spusť test
python3 test_planning_api.py
```

Měl bys vidět:
```
✅ Server is running!
✅ Testing Daily Planning API... Success!
✅ Testing Timeline API... Success!
✅ Testing Weekly Planning API... Success!
✅ Testing Costs API... Success!
✅ Testing Frontend Pages... Success!
```

---

## 💡 Jak přidat testovací data

### Action Item (přes Python)
```python
import requests

requests.post('http://localhost:5000/api/action-items', json={
    'job_id': 1,
    'title': 'Objednat dlažbu',
    'category': 'material',
    'deadline': '2026-01-10',
    'priority': 'high'
})
```

### Material Delivery
```python
requests.post('http://localhost:5000/api/material-delivery', json={
    'job_id': 1,
    'material_name': 'Cement 50kg',
    'quantity': 20,
    'unit': 'pytel',
    'delivery_date': '2026-01-09',
    'supplier': 'Stavebniny XY'
})
```

### Přiřadit zaměstnance
```python
requests.post('http://localhost:5000/api/planning/assign', json={
    'date': '2026-01-08',
    'employee_id': 1,
    'job_id': 1,
    'hours_planned': 8
})
```

---

## 📊 Datový model - co máš navíc

### Nové tabulky:
1. **action_items** - kritické úkoly s deadliny
2. **material_deliveries** - logistika materiálu
3. **daily_plans** - denní plány zaměstnanců
4. **employee_groups** - pro budoucí crew management
5. **planning_conflicts** - auto-detekce kolizí

### Rozšířené tabulky:
- **tasks**: `planned_date`, `planned_end_date`, `estimated_hours`, `actual_cost`
- **jobs**: `start_date_planned`, `weather_check_enabled`

---

## 🔥 Co dál - další features

**Rychle doděláme:**
1. **Timeline view** - Gantt chart všech projektů
2. **Week grid** - týdenní přehled kdo-kde-kdy
3. **Costs view** - přehled nákladů projektů
4. **Modaly** - pro přidávání dat z UI

**Advanced features:**
- Drag & drop plánování
- Počasí API integrace
- Conflict auto-resolution
- Crew management
- Mobile app

---

## ❓ Troubleshooting

### Problém: Migrace failuje
```bash
# Restore backup
cp app.db.backup_before_planning app.db
# Zkus znovu
python3 run_planning_migration.py
```

### Problém: 404 na /planning/daily
1. Check že `planning-daily.html` je v root složce
2. Restart Flask
3. Clear browser cache (Cmd+Shift+R)

### Problém: API vrací prázdná data
Normální - nemáš ještě žádná data. Přidej testovací:
```bash
python3 -c "
import sqlite3
conn = sqlite3.connect('app.db')
conn.execute('''INSERT INTO action_items 
  (job_id, title, category, deadline, priority, created_by)
  VALUES (1, 'Test', 'other', date('now'), 'high', 1)''')
conn.commit()
"
```

---

## 📞 Support

Pokud něco nefunguje:

1. **Check logs:**
   ```bash
   tail -f nohup.out  # pokud používáš nohup
   ```

2. **Browser console:** F12 → Console

3. **Test API přímo:**
   ```bash
   curl http://localhost:5000/api/planning/daily/2026-01-08
   ```

4. **Dokumentace:** `PLANNING_MODULE_INSTALL.md`

---

## 🎉 HOTOVO!

Máš funkční Planning Module.  
Otevři `http://localhost:5000/planning/daily` a začni plánovat! 🚀

**Co máš:**
- ✅ Databázi připravenou
- ✅ Backend API funkční
- ✅ Daily Command Center UI
- ✅ Foundation pro timeline, week, costs views
- ✅ Dokumentaci a testy

**Další krok:**
Zkus to spustit a pak mi řekni co chceš dokončit jako první! 💪
