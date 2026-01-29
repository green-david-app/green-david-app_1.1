# 🌿 GREEN DAVID - UNIFIED SYSTEM

## ✨ CO JSEM UDĚLAL

**SLOUČIL vše do JEDNOHO skladu** s tvým původním designem!

---

## ✅ UNIFIED WAREHOUSE

### **PŮVODNÍ DESIGN** (který máš rád):
- ✅ Stats cards (Celková hodnota, Celkem položek, Nízký stav, Nedostupné)
- ✅ Search bar "Hledat položky..."
- ✅ Filter selecty (kategorie, stav)
- ✅ Tabulka s položkami
- ✅ Historie pohybů
- ✅ Nejpoužívanější položky
- ✅ Export do CSV

### **+ NOVÁ FUNKCIONALITA:**
- ✅ **Příjem/Spotřeba modals**
- ✅ **Propojení s projekty** (spotřeba → zakázka)
- ✅ **Real-time stock tracking**
- ✅ **Database-backed** (ne localStorage)

---

## 🎯 JAK TO FUNGUJE

### **1. PŘIDAT MATERIÁL**
```
Klikni: + Nová položka
→ Vyplň: Název, kategorie, množství, jednotka, cena
→ Uložit
→ ✓ Objeví se v tabulce!
```

### **2. PŘÍJEM MATERIÁLU**
```
U položky klikni: ➕ (zelené tlačítko)
→ Zadej množství
→ Volitelně: cena, poznámka
→ Potvrdit
→ ✓ Stav skladu se zvýší!
```

### **3. SPOTŘEBA NA ZAKÁZCE**
```
U položky klikni: ➖ (červené tlačítko)
→ Zadej množství
→ Vyber ZAKÁZKU ze seznamu
→ Potvrdit
→ ✓ Stav se sníží + propojeno s projektem!
```

---

## 📊 INTEGRACE S PROJEKTY

**Když spotřebuješ materiál na zakázce:**
1. Materiál se odečte ze skladu
2. Spotřeba se zaznamenán v historii
3. **Náklady se propojí s projektem**
4. V Costs Dashboard uvidíš:
   - Práce (timesheets × hourly_rate)
   - + Materiál (movements × unit_price)
   - = Celkové náklady projektu

**Real-time tracking nákladů!**

---

## 🗂️ URL ROUTING

Všechny tyto URL vedou na **STEJNOU stránku**:
- `/warehouse` ← HLAVNÍ
- `/warehouse.html` ← Zpětná kompatibilita
- `/materials` ← Redirect

**Jeden unified systém = `/warehouse`**

---

## 📦 INSTALACE

```bash
cd /Users/greendavid/Desktop/green-david-WORK

# 1. Backup
cp app.db app.db.backup_unified

# 2. Ctrl+C server

# 3. Rozbal ZIP
unzip -o green-david-UNIFIED-WAREHOUSE.zip

# 4. Migrace (pokud ještě neproběhla)
python3 run_extended_migration.py

# 5. Restart
python3 main.py
```

---

## ✅ CO SE STANE

### PŘED:
- Starý warehouse (localStorage)
- Nový materials (nekompatibilní)
- 2 systémy = zmatek

### PO:
- **JEDEN** warehouse
- Tvůj osvědčený design
- + Materials funkcionalita
- Database-backed
- Project tracking
- **Dokonalost!**

---

## 🎨 FEATURES

### PŮVODNÍ (zachováno):
- ✅ Stats dashboard
- ✅ Search & filters
- ✅ Tabulka položek
- ✅ Historie pohybů
- ✅ Top položky
- ✅ Export CSV

### NOVÉ (přidáno):
- ✅ **Příjem/Spotřeba modals**
- ✅ **Propojení s projekty**
- ✅ **Database persistence**
- ✅ **Real-time updates**
- ✅ **Material movements tracking**

---

## 📋 API ENDPOINTS

```
GET  /api/materials              → Seznam položek
POST /api/materials              → Přidat položku
POST /api/materials/movement     → Příjem/Spotřeba
GET  /api/materials/movements    → Historie pohybů
```

---

## 🎯 POUŽITÍ

### Pro inventuru:
```
Warehouse → Přehled všech položek
→ Stats ukazují celkovou hodnotu
→ Alerts na nízký stav
```

### Pro příjem dodávky:
```
Warehouse → Najdi položku → ➕ Příjem
→ Zadej množství a cenu
→ Historie se aktualizuje
```

### Pro zakázku:
```
Warehouse → Najdi materiál → ➖ Spotřeba
→ Vyber zakázku
→ Náklady se propojí s projektem!
```

---

## 🔥 VÝHODY UNIFIED SYSTÉMU

1. **Jeden zdroj pravdy** - vše na jednom místě
2. **Tvůj osvědčený UX** - žádná změna pracovního toku
3. **+ Pokročilé funkce** - project tracking bez složitosti
4. **Database-backed** - žádné ztráty dat
5. **Real-time** - okamžité aktualizace

---

## 🎉 HOTOVO!

**JEDEN dokonalý sklad s tvým designem + Materials funkcionalitou!**

Žádné duplikáty. Žádné konflikty. Prostě funguje! 🌿
