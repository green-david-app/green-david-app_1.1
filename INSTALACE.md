# ⚡ INSTALACE - NAHRAJ A SPUSŤ

## 🎯 Co máš ke stažení

✅ **VŠECHNY OPRAVENÉ SOUBORY** - stačí nahrát a hotovo!

```
📦 Stažené soubory:
├── main.py                              ← OPRAVENÝ backend (s novými endpointy)
├── job-detail.html                      ← OPRAVENÝ detail zakázky (s editací)
├── warehouse.html                       ← Sklad (žádná změna, jen pro jistotu)
├── warehouse_extended.py                ← Warehouse modul (žádná změna)
├── migration_warehouse_jobs_fix.sql     ← SQL migrace DO DATABÁZE
├── static/                              ← Celá složka static (včetně autocomplete JS)
└── README_OPRAVA_SKLADU.md              ← Podrobný návod
```

---

## 🚀 INSTALACE VE 3 KROCÍCH

### KROK 1: Nahraj soubory (PŘEPIŠ všechny)

```bash
# V Render.com nebo na serveru:
cd /path/to/green-david-WORK

# PŘEPIŠ tyto soubory:
# - main.py
# - job-detail.html  
# - warehouse.html
# - warehouse_extended.py
# - celou složku static/
```

**DŮLEŽITÉ:** Soubory **PŘEPIŠ**, ne jen přidej k nim!

---

### KROK 2: Spusť SQL migraci

```bash
# Připoj se k databázi
sqlite3 instance/green_david.db

# Spusť SQL skript
.read migration_warehouse_jobs_fix.sql

# Zkontroluj že se sloupec přidal
.schema warehouse_items
# Měl by obsahovat: reserved_qty REAL DEFAULT 0

# Zkontroluj triggery
SELECT name FROM sqlite_master WHERE type='trigger';
# Měly by být: trg_job_materials_reserve_insert, update, delete

.quit
```

**Nebo jednoduše:**
```bash
sqlite3 instance/green_david.db < migration_warehouse_jobs_fix.sql
```

---

### KROK 3: Restartuj server

```bash
# Render.com: automaticky se restartuje po nahrání

# Lokálně:
python main.py
# nebo
flask run
```

---

## ✅ TESTOVÁNÍ

### Test 1: Autocomplete
1. Otevři detail zakázky: `/job-detail.html?id=X`
2. Klikni "Přidat materiál"
3. Začni psát "stipa"
4. **Měly by se zobrazit návrhy ze skladu** ✨

### Test 2: Editace
1. V detailu zakázky klikni na množství materiálu
2. Změň hodnotu, stiskni Enter
3. **Hodnota by se měla změnit** ✨

### Test 3: Rezervace
1. Přidej materiál ze skladu k zakázce
2. Jdi do skladu: `/warehouse.html`
3. U položky by mělo být: **"🔒 5 ks rezerv. | ✅ 15 ks dost."** ✨

---

## 📋 CHECKLIST

- [ ] Nahrál jsem **main.py** (přepsal, ne přidal!)
- [ ] Nahrál jsem **job-detail.html** (přepsal!)
- [ ] Nahrál jsem složku **static/** (celou)
- [ ] Spustil jsem **migration_warehouse_jobs_fix.sql** v databázi
- [ ] Zkontroloval jsem že triggery existují
- [ ] Restartoval jsem server
- [ ] Otestoval jsem autocomplete (funguje ✅)
- [ ] Otestoval jsem editaci (funguje ✅)
- [ ] Zkontroloval jsem rezervace v skladu (zobrazují se ✅)

---

## 🐛 Když něco nefunguje

### Autocomplete nezobrazuje návrhy
```bash
# Zkontroluj že static/js/job-materials-autocomplete.js existuje
ls static/js/job-materials-autocomplete.js

# Zkontroluj v prohlížeči (F12 Console) jestli se načetl
# Mělo by být: "✅ Material autocomplete loaded"
```

### Rezervace se neaktualizují
```bash
# Zkontroluj triggery v databázi
sqlite3 instance/green_david.db
SELECT name FROM sqlite_master WHERE type='trigger';

# Měly by být 3 triggery:
# - trg_job_materials_reserve_insert
# - trg_job_materials_reserve_update  
# - trg_job_materials_reserve_delete
```

### Editace nefunguje
```bash
# Zkontroluj že main.py obsahuje nové endpointy
grep "api_job_material_update" main.py
grep "api_job_material_delete" main.py

# Pokud NE, přepiš main.py znovu!
```

### Chyba "reserved_qty doesn't exist"
```bash
# Spusť migraci znovu
sqlite3 instance/green_david.db < migration_warehouse_jobs_fix.sql
```

---

## 📞 Podpora

Pokud máš problém:
1. Otevři konzoli prohlížeče (F12) a hledej červené chyby
2. Zkontroluj Flask logy
3. Ověř že jsi přepsal (ne přidal!) všechny soubory
4. Přečti si README_OPRAVA_SKLADU.md

---

## 🎉 TO JE VŠECHNO!

Po těchto 3 krocích by mělo všechno fungovat:
- ✅ Autocomplete materiálů
- ✅ Rezervace ze skladu
- ✅ Editace množství/ceny/dodavatele
- ✅ Statusy materiálů
- ✅ Automatické uvolnění rezervací

**Enjoy! 🚀**

---

**Verze:** 1.0  
**Datum:** 28.1.2026  
**Autor:** Claude + David  
**Status:** ✅ PRODUCTION READY
