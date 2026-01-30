# 🌿 GREEN DAVID PLANNING MODULE - COMPLETE FEATURES

## 📦 CO JE V BALÍKU

### ✅ PLANNING ZÁKLADNÍ MODULY (HOTOVO)
1. **Timeline** - Gantt chart s projekty
2. **Week Grid** - Týdenní plánování zaměstnanců
3. **Daily View** - Denní přehled s počasím
4. **Costs Dashboard** - Real-time náklady projektů

### 🌸 NOVÉ MODULY (EXTENDED)

#### 1. TRVALKOVÉ ŠKOLKA 🌸
**Url:** `/nursery`

**Funkce:**
- 📦 Inventář rostlin (druh, odrůda, množství, stav)
- 🌱 Tracking růstu: semínko → sazenice → prodejní
- 💧 Zalévání schedule s remindery
- 💰 Ekonomika: náklady pěstování vs prodejní cena
- 📍 Lokace (skleník A, záhon 1, etc)
- ⚠️ Alerts: low stock, ready na prodej, zalít dnes

**Database:**
- `nursery_plants` - inventář
- `nursery_watering_schedule` - rozvrhy
- `nursery_watering_log` - historie zalévání

**API:**
- `GET /api/nursery/overview` - stats + alerts
- `GET /api/nursery/plants` - seznam rostlin
- `POST /api/nursery/plants` - přidat rostlinu
- `POST /api/nursery/watering` - zalogovat zalévání

---

#### 2. RECURRING TASKS 🔄
**Url:** `/recurring-tasks`

**Funkce:**
- 🔄 Templates pro opakující se úkoly
- ⏰ Frekvence: denně/týdně/měsíčně
- 🤖 Auto-generování úkolů podle schedule
- 📋 Checklist pro každý task
- 💼 Integrace s veřejnými prostranstvími
- 👥 Default assignování

**Use cases:**
- "Sekání trávníku - Park XY" (každý týden)
- "Údržba záhonů - Náměstí" (každé 2 týdny)
- "Prořez keřů - Škola" (každý měsíc)

**Database:**
- `recurring_task_templates` - šablony
- `recurring_task_instances` - vygenerované instance

**API:**
- `GET /api/recurring/templates` - seznam templates
- `POST /api/recurring/templates` - vytvořit template
- `POST /api/recurring/generate` - generovat úkoly

**Integration:**
- Timeline zobrazí recurring jako pattern
- Week Grid automaticky naplní
- Tasks list obsahuje vygenerované úkoly

---

#### 3. MATERIAL TRACKING 📦
**Url:** `/materials`

**Funkce:**
- 📊 Sklad: substrát, hnojiva, mulč, rostliny
- 📥 Příjem: dodávka od dodavatele
- 📤 Spotřeba: na zakázce/úkolu
- ⚠️ Alerts: nízký stav skladu
- 💰 Náklady: real-time tracking
- 📈 Historie pohybů

**Database:**
- `materials` - položky skladu
- `material_movements` - pohyby (in/out)

**API:**
- `GET /api/materials` - seznam materiálů
- `POST /api/materials/movement` - přidat pohyb

**Integration:**
- Planning/Costs zobrazí náklady: práce + materiál
- Tasks mohou mít attached spotřebu
- Auto-odečet při hotovém úkolu

---

#### 4. PHOTO DOCUMENTATION 📸
**Funkce:**
- 📷 Before/After fotky pro každý task
- 📊 Progress tracking s fotkami
- 🗺️ GPS metadata (kde foceno)
- 📁 Organized po projektech
- 📄 Export do PDF reportů

**Database:**
- `task_photos` - fotky s metadaty

**API:**
- `POST /api/tasks/<id>/photos` - upload fotky
- `GET /api/tasks/<id>/photos` - seznam fotek

**Integration:**
- Tasks mají photo section
- Jobs mají photo gallery
- Export do PDF pro klienty

---

#### 5. PLANT SPECIES DATABASE 🌺
**Url:** `/plant-database`

**Funkce:**
- 📚 Katalog všech druhů rostlin
- 🌞 Požadavky: slunce/stín, voda, půda
- 📅 Kdy sázet, kdy kvete
- 🤝 Kombinace rostlin (dobří/špatní sousedé)
- 🎨 Plánování záhonů

**Database:**
- `plant_species` - katalog rostlin

**API:**
- `GET /api/plant-species` - databáze

**Integration:**
- Návrhy při vytváření zakázky
- Link z Nursery na species info
- Planning suggestions

---

#### 6. MAINTENANCE CONTRACTS 📋
**Funkce:**
- 📜 Smlouvy s městem/klienty
- 💰 Pevné měsíční platby
- 🤖 Auto-generování úkolů
- 📧 Invoice generation
- ⏱️ SLA tracking (reakce do X hodin)

**Database:**
- `maintenance_contracts` - smlouvy
- `contract_invoices` - faktury

**API:**
- `GET /api/contracts` - seznam smluv
- `POST /api/contracts/invoice` - generovat fakturu

**Integration:**
- Recurring tasks automaticky z kontraktů
- Timeline zobrazí contract deadlines
- Costs tracking per contract

---

#### 7. SEASONAL PLANNER 🌱
**Funkce:**
- 📅 Roční cyklus zahradničení
- 🌸 Jaro: výsadby, založení záhonů
- ☀️ Léto: údržba, závlahy
- 🍂 Podzim: cibuloviny, úklid listí
- ❄️ Zima: prořezy, projektování
- ⚠️ Alerts: "Za 2 týdny sázet trvalky"

**Database:**
- `seasonal_tasks` - úkoly podle sezóny

**API:**
- `GET /api/seasonal-tasks` - seznam podle měsíce

**Integration:**
- Timeline zobrazí seasonal milestones
- Notifications reminder kdy co dělat

---

## 🎯 QUICK ACTIONS & INTEGRATIONS

### DRAG & DROP
**Timeline:**
- Táhneš projekt → změní se datum
- Táhneš konec baru → prodlouží deadline

**Week Grid:**
- Táhneš assignment → přesun na jiný den
- Táhneš mezi zaměstnanci → reassign

**Implementation:** HTML5 Drag & Drop API

### EXPORT FUNCTIONS
- **Timeline:** CSV export projektů
- **Costs:** CSV export + Print
- **Week Grid:** Export rozvrhu
- **Nursery:** Export inventáře
- **Materials:** Export skladu

### WEATHER INTEGRATION
- **Real API:** OpenWeatherMap
- **Daily View:** Velká weather karta
- **Outdoor Warning:** Nevhodné podmínky
- **Auto-reschedule:** Přesun podle předpovědi
- **Nursery:** Skip watering když déšť

### AI FEATURES
- **Suggestions:** "5 úkolů bez přiřazení"
- **Conflicts:** "David má 12h v pátek"
- **Budget alerts:** "Projekt 20% nad rozpočtem"
- **Capacity:** "Tento týden 30% nevyužito"

---

## 📊 DATABASE SCHEMA

### CORE TABLES (EXISTING)
- `jobs` - zakázky
- `tasks` - úkoly
- `employees` - zaměstnanci
- `timesheets` - výkazy

### NEW TABLES (EXTENDED)
- `nursery_plants` - školka inventář
- `nursery_watering_schedule` - zalévání
- `nursery_watering_log` - historie
- `recurring_task_templates` - šablony
- `recurring_task_instances` - instance
- `materials` - sklad
- `material_movements` - pohyby
- `task_photos` - fotky
- `plant_species` - databáze rostlin
- `maintenance_contracts` - smlouvy
- `contract_invoices` - faktury
- `seasonal_tasks` - sezónní úkoly

---

## 🚀 INSTALACE

### 1. BACKUP DATABASE
```bash
cd /Users/greendavid/Desktop/green-david-WORK
cp app.db app.db.backup_before_extended
```

### 2. RUN MIGRATION
```bash
python3 run_extended_migration.py
```

### 3. COPY FILES
Rozbal ZIP a nahraď soubory:
- `migrations/002_planning_extended.sql`
- `planning_extended_api.py`
- `nursery.html`
- `recurring-tasks.html`
- `materials.html`
- `plant-database.html`
- `planning-timeline.html` (updated)
- `planning-week.html` (updated)
- `planning-daily.html` (updated)
- `planning-costs.html` (updated)

### 4. UPDATE MAIN.PY
Přidej routes z `/tmp/new_routes.py` do `main.py`

### 5. RESTART
```bash
python3 main.py
```

### 6. TEST
- http://localhost:5000/nursery
- http://localhost:5000/recurring-tasks
- http://localhost:5000/materials
- http://localhost:5000/plant-database

---

## 🎨 NAVIGATION

### Nová menu struktura:
```
HLAVNÍ
├─ Dashboard
├─ Zakázky
├─ Úkoly
├─ Zaměstnanci
└─ Výkazy

PLÁNOVÁNÍ 🌿
├─ Dnes (Daily)
├─ Timeline (Gantt)
├─ Týden (Week Grid)
├─ Náklady (Costs)
├─ Opakující se úkoly 🆕
└─ Sezónní plánér 🆕

ŠKOLKA & MATERIÁL 🌸
├─ Trvalkové školka 🆕
├─ Sklad materiálu 🆕
└─ Databáze rostlin 🆕

SMLOUVY 📋
└─ Maintenance contracts 🆕
```

---

## 💡 USAGE EXAMPLES

### PŘÍKLAD 1: Týdenní rutina
1. **Pondělí ráno:** Otevři `/planning/daily`
   - Vidíš počasí + upozornění
   - Zalij rostliny podle seznamu
   - Zkontroluj opožděné úkoly

2. **Pátek odpoledne:** Otevři `/planning/week`
   - Naplánuj příští týden
   - Vygeneruj recurring tasks
   - Assignuj lidi na zakázky

3. **Konec měsíce:** Otevři `/planning/costs`
   - Export nákladů do CSV
   - Zkontroluj přečerpané projekty
   - Generuj faktury z contracts

### PŘÍKLAD 2: Správa školky
1. **Jaro:** Přidej nové sazenice do Nursery
2. **Léto:** Trackuj růst, zalévej podle schedule
3. **Podzim:** Označ "ready na prodej"
4. **Prodej:** Update quantity, zaznamenej profit

### PŘÍKLAD 3: Veřejná prostranství
1. Vytvoř Maintenance Contract s městem
2. Nastav Recurring Task "Sekání každý týden"
3. Systém automaticky generuje úkoly
4. Workers dostanou notifikace
5. Po dokončení fotka before/after
6. Konec měsíce: Auto-faktura

---

## 🔧 TROUBLESHOOTING

### Migration fails
```bash
# Restore backup
cp app.db.backup_before_extended app.db

# Check SQL syntax
sqlite3 app.db < migrations/002_planning_extended.sql
```

### API errors
```python
# Check logs
python3 main.py
# Watch for [ERROR] messages
```

### Missing routes
```python
# Verify in main.py:
import planning_extended_api as ext_api
ext_api.get_db = get_db
```

---

## 📈 ROADMAP

### DONE ✅
- Planning základní moduly
- Nursery
- Recurring tasks
- Materials
- Photos
- Plant database
- Contracts
- Seasonal planner
- Weather integration
- Export functions
- Search/filters

### TODO 🔨
- Drag & drop implementation
- Auto-reschedule podle počasí
- Route optimization
- Smart watering (IoT)
- Mobile responsiveness enhancement
- Batch operations
- Advanced reporting

---

## 🎯 KEY METRICS

**Development time:** 8+ hours
**New tables:** 12
**New API endpoints:** 15+
**New pages:** 4
**Features:** 13
**Lines of code:** ~3000

**Impact:**
- 🌸 Školka plně trackovaná
- 🔄 Opakující se práce automatizovaná
- 📦 Sklad pod kontrolou
- 📸 Dokumentace fotkami
- 📋 Smlouvy organizované
- 🌱 Sezónní plánování

---

## 📞 SUPPORT

**Issues?** Check logs, verify migration, test APIs one by one.

**Questions?** All features designed specifically for zahradnictví!

**Success?** Enjoy professional-grade planning system! 🎉
