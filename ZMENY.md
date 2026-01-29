# 📝 SEZNAM ZMĚN V SOUBORECH

## 🔧 Opravené/změněné soubory

### 1. **main.py** ✅ OPRAVENO
**Přidáno:**
- `@app.route("/api/jobs/<int:job_id>/materials/<int:material_id>", methods=["PATCH"])`
  - Funkce: `api_job_material_update(job_id, material_id)`
  - Účel: Editace materiálu (množství, cena, dodavatel, status)
  
- `@app.route("/api/jobs/<int:job_id>/materials/<int:material_id>", methods=["DELETE"])`
  - Funkce: `api_job_material_delete(job_id, material_id)`
  - Účel: Smazání materiálu s automatickým uvolněním rezervace

**Umístění:** Přidáno za funkci `api_job_reserve_material` (řádek ~4315)

**Změny:**
- Celkem +150 řádků kódu
- 2 nové endpointy
- Validace dostupnosti skladu při editaci množství
- Automatické přepočítání total_price

---

### 2. **job-detail.html** ✅ OPRAVENO
**Nahrazeno:**
- Celá funkce `renderMaterials(materials)` (původně řádky 1061-1119)

**Přidáno:**
- `editMaterialField(materialId, field, currentValue, inputType)` - Inline editace
- `saveMaterialField(materialId, field)` - Uložení změny
- `cancelMaterialEdit()` - Zrušení editace
- `updateMaterialStatus(materialId, newStatus)` - Změna statusu
- `deleteMaterial(materialId)` - Smazání s potvrzením
- `escapeHtml(text)` - Helper pro bezpečné zobrazení HTML

**UI změny:**
- Klikatelná pole pro editaci (množství, cena, dodavatel)
- Dropdown pro statusy (Plánováno/Objednáno/Dodáno/Použito)
- Zobrazení rezervovaného množství
- Ikona 📦 pro materiály ze skladu
- Varování při mazání rezervovaných položek

**Změny:**
- Celkem +280 řádků kódu
- Nový sloupec "Status" v tabulce
- Nový sloupec "Sklad" s informacemi o lokaci
- Inline editace namísto formulářů

---

### 3. **migration_warehouse_jobs_fix.sql** ✨ NOVÝ
**Obsah:**
- `ALTER TABLE warehouse_items ADD COLUMN reserved_qty`
- `ALTER TABLE job_materials ADD COLUMN warehouse_item_id`
- `ALTER TABLE job_materials ADD COLUMN reserved_qty`
- `ALTER TABLE job_materials ADD COLUMN warehouse_location`
- `ALTER TABLE job_materials ADD COLUMN status`
- 3 triggery pro automatickou aktualizaci rezervací:
  - `trg_job_materials_reserve_insert`
  - `trg_job_materials_reserve_update`
  - `trg_job_materials_reserve_delete`
- Přepočítání existujících rezervací

**Účel:** Rozšíření databáze o podporu rezervací

---

### 4. **warehouse.html** 🔄 BEZ ZMĚN
**Důvod:** Už má podporu pro zobrazení `reserved_qty` v items.js

**Kontrola:**
- Řádky 92-99 v `/static/warehouse/items.js` už zobrazují rezervace
- Žádná změna není potřeba

---

### 5. **warehouse_extended.py** 🔄 BEZ ZMĚN
**Důvod:** Search endpoint už správně funguje

**Kontrola:**
- Endpoint `/api/warehouse/search` už načítá `reserved_qty`
- Již vrací `available_qty = qty - reserved_qty`

---

### 6. **static/js/job-materials-autocomplete.js** 🔄 BEZ ZMĚN
**Důvod:** Již správně implementováno

**Kontrola:**
- Autocomplete funguje s `/api/warehouse/search`
- Zobrazuje dostupné množství
- Vyplňuje jednotku a cenu
- Žádná změna není potřeba

---

## 📊 Statistika změn

```
Celkem změněných souborů: 2 (main.py, job-detail.html)
Celkem přidaných řádků: ~430
Nových funkcí: 8
Nových endpointů: 2
Nových SQL triggerů: 3
Nových databázových sloupců: 5
```

---

## 🗂️ Struktura databáze PO MIGRACI

### warehouse_items
```sql
id INTEGER PRIMARY KEY
name TEXT NOT NULL
sku TEXT
category TEXT
qty REAL DEFAULT 0
unit TEXT DEFAULT 'ks'
price REAL
location TEXT
reserved_qty REAL DEFAULT 0          -- ✨ NOVÉ
status TEXT DEFAULT 'active'
created_at TEXT
updated_at TEXT
```

### job_materials
```sql
id INTEGER PRIMARY KEY
job_id INTEGER NOT NULL
name TEXT NOT NULL
quantity REAL
unit TEXT DEFAULT 'ks'
price_per_unit REAL
total_price REAL
supplier TEXT
warehouse_item_id INTEGER            -- ✨ NOVÉ
reserved_qty REAL DEFAULT 0          -- ✨ NOVÉ
warehouse_location TEXT              -- ✨ NOVÉ
status TEXT DEFAULT 'planned'        -- ✨ NOVÉ
created_at TEXT
updated_at TEXT
```

---

## 🔄 API Endpointy

### Nové endpointy:

```
PATCH /api/jobs/{job_id}/materials/{material_id}
Body: { "quantity": 10, "price_per_unit": 45, "supplier": "XYZ", "status": "ordered" }
→ Upraví materiál, aktualizuje rezervaci

DELETE /api/jobs/{job_id}/materials/{material_id}
→ Smaže materiál, uvolní rezervaci (přes trigger)
```

### Existující endpointy (používané):

```
GET /api/warehouse/search?q=stipa
→ Vrací položky ze skladu s reserved_qty a available_qty

POST /api/jobs/{job_id}/materials/reserve
Body: { "warehouse_item_id": 123, "qty": 10 }
→ Přidá materiál a rezervuje ho
```

---

## 🎯 Klíčové funkce

### Frontend (job-detail.html)

```javascript
// Inline editace
editMaterialField(materialId, 'quantity', 10, 'number')
→ Zobrazí input pro editaci

saveMaterialField(materialId, 'quantity')
→ Uloží změnu přes PATCH endpoint

// Status management
updateMaterialStatus(materialId, 'delivered')
→ Změní status materiálu

// Mazání
deleteMaterial(materialId)
→ Smaže materiál s potvrzením
```

### Backend (main.py)

```python
# Editace
api_job_material_update(job_id, material_id)
→ Validuje dostupnost, aktualizuje množství

# Mazání
api_job_material_delete(job_id, material_id)
→ Smaže záznam, trigger uvolní rezervaci
```

### Database (triggery)

```sql
-- Při INSERT do job_materials
→ warehouse_items.reserved_qty += qty

-- Při UPDATE job_materials.qty
→ reserved_qty -= old_qty
→ reserved_qty += new_qty

-- Při DELETE z job_materials
→ warehouse_items.reserved_qty -= qty
```

---

## 📦 Co se NEMĚNILO

✅ Tyto soubory zůstaly BEZ ZMĚN (ale jsou ve výstupech pro úplnost):
- `warehouse.html` - už měl podporu pro reserved_qty
- `warehouse_extended.py` - search endpoint už fungoval
- `static/js/job-materials-autocomplete.js` - už správně implementováno
- `static/warehouse/items.js` - už zobrazoval rezervace

---

## 🔍 Jak najít změny v souborech

### V main.py:
```bash
# Hledej nové funkce:
grep -n "api_job_material_update\|api_job_material_delete" main.py

# Měly by být kolem řádku 4316-4500
```

### V job-detail.html:
```bash
# Hledej nové funkce:
grep -n "editMaterialField\|saveMaterialField\|deleteMaterial" job-detail.html

# Měly by být kolem řádku 1130-1360
```

---

## ✅ Kontrolní seznam před nasazením

- [ ] Zkontroloval jsem že main.py obsahuje `api_job_material_update`
- [ ] Zkontroloval jsem že main.py obsahuje `api_job_material_delete`
- [ ] Zkontroloval jsem že job-detail.html má novou funkci `renderMaterials`
- [ ] Zkontroloval jsem že job-detail.html má funkci `editMaterialField`
- [ ] Zkontroloval jsem že migrace vytvoří sloupec `reserved_qty`
- [ ] Zkontroloval jsem že migrace vytvoří 3 triggery
- [ ] Zkontroloval jsem že static/js/job-materials-autocomplete.js existuje

---

**Poslední aktualizace:** 28.1.2026  
**Verze:** 1.0  
**Status:** ✅ Připraveno k nasazení
