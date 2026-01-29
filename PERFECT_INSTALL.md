# 🌿 GREEN DAVID - PERFEKTNÍ SYSTÉM

## ✨ CO JE TO

**Jeden** unified, propojený, dokonalý planning system pro zahradnictví.

**ŽÁDNÉ duplikáty. ŽÁDNÉ konflikty. Všechno dokonalé.**

---

## 🎯 CO MÁŠ

### ✅ **CORE PLANNING**
- Daily View (počasí + notifications)
- Timeline (Gantt chart)
- Week Grid (capacity planning)
- Costs Dashboard (real-time)

### ✅ **NURSERY** 🌸
- Kompletní inventář rostlin
- Zalévání schedule
- Tracking růstu
- Ekonomika skladu
- **PLNĚ FUNKČNÍ MODAL PRO PŘIDÁNÍ**

### ✅ **MATERIALS** 📦  
- **NAHRAZUJE WAREHOUSE!**
- Propojený s projekty
- Tracking spotřeby
- Low stock alerts
- **PLNĚ FUNKČNÍ MODALS**

### ✅ **RECURRING TASKS** 🔄
- Templates pro opakování
- Auto-generation
- Integration s projekty

### ✅ **OSTATNÍ**
- Photo documentation
- Plant database
- Seasonal planner
- Maintenance contracts

---

## 🚀 INSTALACE (3 MINUTY)

### KROK 1: BACKUP
```bash
cd /Users/greendavid/Desktop/green-david-WORK
cp app.db app.db.backup_perfect_$(date +%Y%m%d)
```

### KROK 2: ZASTAV SERVER
```
Ctrl+C v terminálu
```

### KROK 3: ROZBAL ZIP
```bash
unzip -o green-david-PERFECT-SYSTEM.zip
```

**Přepíše:**
- `nursery-complete.html` (nový)
- `materials-complete.html` (nový)
- `main.py` (updated routes)
- `planning_extended_api.py` (create endpoints)
- `index.html` (menu karty)
- Všechny planning HTML (enhanced)

### KROK 4: SPUSŤ MIGRACI
```bash
python3 run_extended_migration.py
```

**Výstup:**
```
[Migration] ✅ SUCCESS - Extended features installed!
[Verify] New tables: nursery_plants, materials, ...
```

### KROK 5: RESTART
```bash
python3 main.py
```

**Výstup:**
```
✅ Jobs Extended API loaded
✅ Planning Module loaded
✅ Planning Extended Routes loaded
* Running on http://127.0.0.1:5000
```

### KROK 6: OTEVŘI BROWSER
```
http://127.0.0.1:5000
```

---

## ✅ CO VIDÍŠ NA HLAVNÍ STRÁNCE

```
┌─────────────┬─────────────┬─────────────┐
│ Zakázka     │ Výkaz       │ Zakázky     │
├─────────────┼─────────────┼─────────────┤
│ Úkoly       │ Tým         │ Plánování   │
├─────────────┼─────────────┼─────────────┤
│ 🌸 Školka   │ 🔄 Recurring│ 📦 Sklad    │ ← NOVÉ KARTY
└─────────────┴─────────────┴─────────────┘
```

---

## 🎯 TEST FLOW

### 1. ŠKOLKA
```
Klikni: 🌸 Školka
→ Klikni: + Přidat rostlinu
→ Vyplň: Echinacea purpurea, 10 ks, sazenice
→ Klikni: Přidat rostlinu
→ ✓ Vidíš kartu s rostlinou!
```

### 2. MATERIÁLY
```
Klikni: 📦 Sklad
→ Klikni: + Přidat materiál
→ Vyplň: Substrát univerzální, 100 kg
→ Klikni: Přidat
→ ✓ Vidíš kartu s materiálem!
→ Klikni: ➕ Příjem
→ Přidej: 50 kg
→ ✓ Stav skladu: 150 kg!
```

### 3. RECURRING
```
Klikni: 🔄 Recurring
→ Vytvoř template: "Sekání trávníku"
→ Frekvence: Týdně
→ Klikni: ⚡ Generovat úkoly
→ ✓ Úkol vytvořen!
```

---

## 📊 DATABASE STRUKTURA

### ✅ EXISTUJÍCÍ (nezměněno)
- `jobs` - zakázky
- `tasks` - úkoly
- `employees` - zaměstnanci
- `timesheets` - výkazy

### ✅ NOVÉ (přidáno)
- `nursery_plants` - školka
- `nursery_watering_schedule` 
- `nursery_watering_log`
- `materials` - **UNIFIED SKLAD**
- `material_movements`
- `recurring_task_templates`
- `recurring_task_instances`
- `task_photos`
- `plant_species`
- `maintenance_contracts`
- `contract_invoices`
- `seasonal_tasks`

---

## 🔍 INTEGRACE

### Materials → Jobs
```
Spotřeba materiálu se propojí s zakázkou
→ Real-time náklady v Costs Dashboard
```

### Nursery → Materials
```
Rostliny z nursery můžeš použít jako materiál
→ Tracking: školka → zakázka
```

### Recurring → Tasks
```
Template generuje skutečné tasks
→ Vidíš je v Tasks list
→ Assignované lidem
```

---

## ⚠️ DŮLEŽITÉ

### WAREHOUSE JE DEPRECATED
- Starý `/warehouse.html` můžeš smazat
- Nebo nechat pro historická data
- Nový systém = **Materials** (`/materials`)

### SESSION HANDLING
- API používá `session.get('user_id', 1)`
- Fallback na user_id=1
- Funguje i bez přihlášení (pro testing)

### ŽÁDNÉ PLACEHOLDERS
- Všechny modals fungují
- Všechny endpoints existují
- Všechno propojené

---

## 🎉 ENJOY!

Máš **profesionální**, **unified**, **dokonalý** systém!

**Žádné duplikáty. Žádné konflikty. Všechno propojené. 🌿**
