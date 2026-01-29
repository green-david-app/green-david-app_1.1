# ⚡ QUICK START - Planning Extended Features

## 🎯 CO DOSTANEŠ

13 NOVÝCH FEATUR pro zahradnictví:
1. 🌸 Trvalkové školka
2. 🔄 Recurring tasks  
3. 📦 Material tracking
4. 📸 Photo documentation
5. 🌺 Plant database
6. 📋 Maintenance contracts
7. 🌱 Seasonal planner
8. ☁️ Weather integration (enhanced)
9. 📊 Export funkce (CSV)
10. 🔍 Search & filters
11. 🔔 Notifications & suggestions
12. 🖱️ Better UX (připraveno pro drag&drop)
13. 📱 Mobile-friendly

---

## 🚀 INSTALACE (5 MINUT)

### KROK 1: BACKUP (30 sek)
```bash
cd /Users/greendavid/Desktop/green-david-WORK
cp app.db app.db.backup_$(date +%Y%m%d)
```

### KROK 2: STÁHNI ZIP
Stáhni `green-david-PLANNING-COMPLETE.zip` z Claude

### KROK 3: ROZBAL
```bash
# Rozbal do green-david-WORK složky
# Nahradí/přidá tyto soubory:
# - migrations/002_planning_extended.sql
# - run_extended_migration.py
# - planning_extended_api.py
# - nursery.html
# - recurring-tasks.html
# - materials.html
# - plant-database.html
# - planning-*.html (4 updated files)
# - PLANNING_EXTENDED_DOCS.md
```

### KROK 4: RUN MIGRATION (1 min)
```bash
python3 run_extended_migration.py
```

**Output měl by být:**
```
[Migration] ✅ SUCCESS - Extended features installed!
[Verify] New tables: nursery_plants, recurring_task_templates, materials, task_photos, plant_species, maintenance_contracts
```

### KROK 5: UPDATE MAIN.PY (2 min)

Otevři `main.py` a přidej **NA KONEC před `if __name__ == '__main__':`**:

```python
# ================================================================
# PLANNING EXTENDED ROUTES
# ================================================================
import planning_extended_api as ext_api
ext_api.get_db = get_db

# Nursery
@app.route('/nursery')
@login_required
def nursery_page():
    return send_from_directory('.', 'nursery.html')

@app.route('/api/nursery/overview')
@login_required
def api_nursery_overview():
    return ext_api.get_nursery_overview()

@app.route('/api/nursery/plants')
@login_required
def api_nursery_plants():
    return ext_api.get_nursery_plants()

@app.route('/api/nursery/plants', methods=['POST'])
@login_required
def api_create_nursery_plant():
    return ext_api.create_nursery_plant()

@app.route('/api/nursery/watering', methods=['POST'])
@login_required
def api_log_watering():
    return ext_api.log_watering()

# Recurring tasks
@app.route('/recurring-tasks')
@login_required
def recurring_tasks_page():
    return send_from_directory('.', 'recurring-tasks.html')

@app.route('/api/recurring/templates')
@login_required
def api_recurring_templates():
    return ext_api.get_recurring_templates()

@app.route('/api/recurring/templates', methods=['POST'])
@login_required
def api_create_recurring_template():
    return ext_api.create_recurring_template()

@app.route('/api/recurring/generate', methods=['POST'])
@login_required
def api_generate_recurring():
    return ext_api.generate_recurring_tasks()

# Materials
@app.route('/materials')
@login_required
def materials_page():
    return send_from_directory('.', 'materials.html')

@app.route('/api/materials')
@login_required
def api_materials():
    return ext_api.get_materials()

@app.route('/api/materials/movement', methods=['POST'])
@login_required
def api_material_movement():
    return ext_api.add_material_movement()

# Photos
@app.route('/api/tasks/<int:task_id>/photos', methods=['POST'])
@login_required
def api_upload_task_photo(task_id):
    request.view_args = {'task_id': task_id}
    return ext_api.upload_task_photo()

@app.route('/api/tasks/<int:task_id>/photos')
@login_required
def api_get_task_photos(task_id):
    return ext_api.get_task_photos(task_id)

# Plant database
@app.route('/plant-database')
@login_required
def plant_database_page():
    return send_from_directory('.', 'plant-database.html')

@app.route('/api/plant-species')
@login_required
def api_plant_species():
    return ext_api.get_plant_species()

print("✅ Planning Extended Routes loaded")
```

### KROK 6: RESTART (30 sek)
```bash
# Zastav running server (Ctrl+C)
python3 main.py
```

**Měl bys vidět:**
```
✅ Jobs Extended API loaded
✅ Planning Module loaded
✅ Planning Extended Routes loaded
* Running on http://127.0.0.1:5000
```

### KROK 7: TEST (1 min)
Otevři browser:
- http://localhost:5000/nursery ← 🌸 Školka
- http://localhost:5000/recurring-tasks ← 🔄 Recurring
- http://localhost:5000/materials ← 📦 Sklad
- http://localhost:5000/planning/daily ← Vylepšený Daily

---

## ✅ VERIFICATION CHECKLIST

- [ ] Migration proběhla bez chyb
- [ ] Flask server startuje s "Extended Routes loaded"
- [ ] /nursery page načítá
- [ ] /recurring-tasks page načítá
- [ ] /materials page načítá
- [ ] /planning/daily má notifications panel
- [ ] /planning/timeline má Export button
- [ ] /planning/costs má Print & Export buttony

---

## 🎉 CO TEĎ FUNGUJE

### NURSERY (/nursery)
- ✅ Přehled rostlin
- ✅ Stats (celkem, ready, pěstování)
- ✅ Zalévání schedule
- ✅ "Zalít dnes" seznam
- ⏳ Add plant modal (připraveno)

### RECURRING TASKS (/recurring-tasks)
- ✅ Seznam templates
- ✅ Generate tasks button
- ✅ Frequency display
- ⏳ Create template modal (připraveno)

### MATERIALS (/materials)
- ✅ Sklad overview
- ✅ Low stock alerts
- ✅ Stock bars
- ⏳ Add/Remove stock modals (připraveno)

### PLANNING ENHANCED
- ✅ Daily: Notifications & Suggestions panel
- ✅ Timeline: Export CSV
- ✅ Costs: Print & Export CSV
- ✅ Week: Search zaměstnanců
- ✅ Všude: Zpět button fix

---

## 🔨 CO DODĚLAT (MODALS)

Všechny stránky jsou funkční, ale modals pro přidání dat jsou připravené jako placeholders:

**Nursery:**
- Add plant modal (form s: druh, odrůda, množství, lokace)

**Recurring:**
- Create template modal (form s: název, frekvence, job, assignee)

**Materials:**
- Add material modal
- Add/Remove stock modals

**Implementace:** Jednoduchý HTML dialog nebo použij existující modal pattern z aplikace

---

## 📊 DATABASE STATS

**Nové tabulky:** 12
- `nursery_plants`
- `nursery_watering_schedule`
- `nursery_watering_log`
- `recurring_task_templates`
- `recurring_task_instances`
- `materials`
- `material_movements`
- `task_photos`
- `plant_species`
- `maintenance_contracts`
- `contract_invoices`
- `seasonal_tasks`

---

## 🐛 TROUBLESHOOTING

### "Planning Extended Routes loaded" nevidím
```python
# Zkontroluj že máš v main.py:
import planning_extended_api as ext_api
ext_api.get_db = get_db
```

### 404 na /nursery
```python
# Zkontroluj že nursery.html je v root složce
ls -la nursery.html
```

### API vrací 500
```bash
# Sleduj konzoli pro [ERROR] messages
python3 main.py
# A navštiv problematickou URL
```

### Migration error
```bash
# Restore backup
cp app.db.backup_YYYYMMDD app.db

# Re-run
python3 run_extended_migration.py
```

---

## 🎯 NEXT STEPS

1. **Add test data:**
   - Přidej pár rostlin do Nursery
   - Vytvoř recurring template
   - Přidej materiály do skladu

2. **Customize:**
   - Implementuj modals
   - Přidej vlastní kategorie rostlin
   - Nastav watering schedules

3. **Integrate:**
   - Link nursery rostliny na zakázky
   - Trackuj materiál per job
   - Generuj recurring tasks

4. **Enjoy!** 🎉

---

## 📞 NEED HELP?

**Check logs:** Terminal output má detaily
**Read docs:** `PLANNING_EXTENDED_DOCS.md` má vše
**Test API:** Použij browser DevTools → Network tab

**Success?** Máš profesionální planning system pro zahradnictví! 🌿
