# Katalog rostlin - Implementační návod

## 📋 Co to dělá?

Přidává do aplikace **katalog rostlin** s botanickými údaji z konkurenčního ceníku. Když přidáváš rostlinu do školky:
- Začneš psát název → zobrazí se autocomplete seznam z katalogu
- Vyber rostlinu → automaticky se vyplní všechny botanické údaje
- Nebo vytvoř novou rostlinu ručně

## 🗂️ Struktura databáze

Nová tabulka `plant_catalog` obsahuje:
- Latinský název (např. "Aquilegia caerulea")
- Odrůda (např. "Blue Star")
- Velikost kontejneru (např. "K9")
- Barva květu, doba květu, výška
- Nároky na světlo, stanoviště
- Zona mrazuvzdornost
- Poznámky a další údaje

## 🚀 Instalace krok za krokem

### 1. Vytvoř databázovou tabulku

```bash
cd ~/Green-David-App

# Aplikuj migraci
sqlite3 instance/green_david.db < plant_catalog_migration.sql
```

### 2. Importuj data z DOCX

```bash
# Nahraj soubor cenik_celorocni-pereny.docx do složky instance/
cp /path/to/cenik_celorocni-pereny.docx instance/

# Spusť import
python3 import_plant_catalog.py instance/cenik_celorocni-pereny.docx instance/green_david.db
```

Měl bys vidět:
```
✓ Import dokončen!
  Importováno: XXX rostlin
  Přeskočeno: YY (duplicity)
  Chyby: 0
```

### 3. Přidej API endpointy do app.py

Otevři `app.py` a přidej tyto endpointy (nebo zkopíruj z `plant_catalog_api.py`):

```python
# ========== PLANT CATALOG API ==========

@app.route('/api/plant-catalog/search', methods=['GET'])
@login_required
def api_plant_catalog_search():
    """Vyhledávání v katalogu rostlin (autocomplete)"""
    query = request.args.get('q', '').strip()
    limit = request.args.get('limit', 20, type=int)
    
    if not query or len(query) < 2:
        return jsonify({
            'success': False,
            'message': 'Zadej alespoň 2 znaky'
        }), 400
    
    try:
        db = get_db()
        results = db.execute('''
            SELECT pc.id, pc.latin_name, pc.variety, pc.container_size,
                   pc.flower_color, pc.flowering_time, pc.height,
                   pc.light_requirements, pc.hardiness_zone
            FROM plant_catalog_fts fts
            JOIN plant_catalog pc ON pc.id = fts.rowid
            WHERE plant_catalog_fts MATCH ?
            ORDER BY rank
            LIMIT ?
        ''', (f'{query}*', limit)).fetchall()
        
        plants = []
        for row in results:
            full_name = row['latin_name']
            if row['variety']:
                full_name += f" '{row['variety']}'"
            if row['container_size']:
                full_name += f" - {row['container_size']}"
            
            plants.append({
                'id': row['id'],
                'full_name': full_name,
                'latin_name': row['latin_name'],
                'variety': row['variety'],
                'container_size': row['container_size'],
                'flower_color': row['flower_color'],
                'flowering_time': row['flowering_time'],
                'height': row['height'],
                'light_requirements': row['light_requirements'],
                'hardiness_zone': row['hardiness_zone']
            })
        
        return jsonify({
            'success': True,
            'plants': plants,
            'count': len(plants)
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Chyba: {str(e)}'
        }), 500

@app.route('/api/plant-catalog/<int:plant_id>', methods=['GET'])
@login_required
def api_plant_catalog_detail(plant_id):
    """Detail rostliny z katalogu"""
    try:
        db = get_db()
        plant = db.execute('SELECT * FROM plant_catalog WHERE id = ?', (plant_id,)).fetchone()
        
        if not plant:
            return jsonify({'success': False, 'message': 'Nenalezeno'}), 404
        
        return jsonify({'success': True, 'plant': dict(plant)})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500
```

### 4. Přidej JavaScript autocomplete

Zkopíruj `plant_catalog_autocomplete.js` do `static/`:

```bash
cp plant_catalog_autocomplete.js static/
```

### 5. Uprav nursery.html

Přidej do hlavičky:

```html
<script src="/static/plant_catalog_autocomplete.js"></script>
```

Přidej modal pro přidání rostliny (viz `plant_modal_example.html`).

Přidej tlačítko pro otevření modalu:

```html
<button class="btn btn-primary" onclick="openPlantModal()">
    + Přidat rostlinu
</button>
```

### 6. Upravit tabulku nursery_plants

Pokud ještě nemáš tabulku pro rostliny v školce, vytvoř ji:

```sql
CREATE TABLE IF NOT EXISTS nursery_plants (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    latin_name TEXT NOT NULL,
    variety TEXT,
    container_size TEXT,
    -- Botanické údaje
    flower_color TEXT,
    flowering_time TEXT,
    height TEXT,
    light_requirements TEXT,
    leaf_color TEXT,
    hardiness_zone TEXT,
    site_type TEXT,
    plants_per_m2 TEXT,
    botanical_notes TEXT,
    -- Školkařské údaje
    count INTEGER NOT NULL DEFAULT 0,
    location TEXT,
    status TEXT DEFAULT 'sazenice',  -- semínko, sazenice, prodejní
    price REAL,
    planted_date DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

## 📖 Jak to funguje

### Přidání rostliny s autocomplete:

1. Klikneš na "Přidat rostlinu"
2. Do pole "Vyhledat v katalogu" začneš psát např. "aqui"
3. Zobrazí se seznam rostlin:
   ```
   Aquilegia caerulea 'Blue Star' - K9
   ├─ světle modrá, bílá koruna
   ├─ 5-6
   ├─ 60 cm
   └─ Zona 3
   ```
4. Vybereš rostlinu → automaticky se vyplní:
   - Latinský název: Aquilegia caerulea
   - Odrůda: Blue Star
   - Barva květu: světle modrá, bílá koruna
   - Doba květu: 5-6
   - Výška: 60 cm
   - Nároky na světlo: slunce, polostín
   - Zona mrazuvzdornost: 3
   - atd.

5. Jen doplníš:
   - Počet kusů
   - Umístění (Záhon A, Skleník 1...)
   - Stav (semínko/sazenice/prodejní)
   - Cenu
   - Datum nasazení

6. Uložíš → rostlina je v databázi včetně všech botanických údajů

### Ruční přidání:

Pokud rostlina není v katalogu, jednoduše vyplníš všechny údaje ručně.

## 🎨 Vizuální vylepšení

### Zobrazení botanických údajů v detailu rostliny

Přidej do detail karty rostliny:

```html
<div class="botanical-details">
    <h4>🌿 Botanické údaje</h4>
    <div class="info-grid">
        <div class="info-item">
            <span class="label">Barva květu:</span>
            <span class="value">{{plant.flower_color}}</span>
        </div>
        <div class="info-item">
            <span class="label">Doba květu:</span>
            <span class="value">{{plant.flowering_time}}</span>
        </div>
        <div class="info-item">
            <span class="label">Výška:</span>
            <span class="value">{{plant.height}}</span>
        </div>
        <div class="info-item">
            <span class="label">Světlo:</span>
            <span class="value">{{plant.light_requirements}}</span>
        </div>
        <div class="info-item">
            <span class="label">Zona:</span>
            <span class="value">{{plant.hardiness_zone}}</span>
        </div>
    </div>
</div>
```

## 🔧 Údržba katalogu

### Přidání nové rostliny do katalogu

```python
# Manuálně přes SQL
INSERT INTO plant_catalog (latin_name, variety, flower_color, flowering_time, height)
VALUES ('Lavandula angustifolia', 'Hidcote', 'tmavě fialová', '6-8', '30-40 cm');
```

### Aktualizace údajů

```python
UPDATE plant_catalog 
SET height = '40-50 cm', flower_color = 'sytě fialová'
WHERE latin_name = 'Lavandula angustifolia' AND variety = 'Hidcote';
```

### Smazání rostliny z katalogu

```python
DELETE FROM plant_catalog 
WHERE latin_name = 'Název' AND variety = 'Odrůda';
```

## 📊 Statistiky

Kolik máš rostlin v katalogu:

```sql
SELECT 
    COUNT(*) as celkem_rostlin,
    COUNT(DISTINCT latin_name) as druhů,
    COUNT(DISTINCT CASE WHEN variety IS NOT NULL THEN latin_name END) as s_odrůdami
FROM plant_catalog;
```

## 🐛 Možné problémy

**Autocomplete nefunguje:**
- Zkontroluj, že je `plant_catalog_autocomplete.js` správně načtený
- Otevři Console v prohlížeči (F12) a hledej chyby
- Zkontroluj, že API endpoint `/api/plant-catalog/search` funguje

**Import selhal:**
- Zkontroluj, že máš nainstalovaný `python-docx`: `pip3 install python-docx`
- Zkontroluj cestu k DOCX souboru a databázi

**FTS search nefunguje:**
- Zkontroluj, že SQLite podporuje FTS5
- Zkus znovu aplikovat migraci

## 💡 Tipy

1. **Obrázky rostlin**: Můžeš přidat sloupec `image_url` do `plant_catalog` a zobrazovat obrázky v autocomplete

2. **České názvy**: Přidej sloupec `czech_name` pro vyhledávání v češtině

3. **Kategorie**: Přidej `category` (trvalky, traviny, kapradiny...) pro filtrování

4. **Export ceníku**: Vytvoř endpoint pro export vlastního ceníku z databáze

## ✅ Checklist implementace

- [ ] Aplikovat SQL migraci
- [ ] Importovat data z DOCX
- [ ] Přidat API endpointy do app.py
- [ ] Zkopírovat JavaScript soubor
- [ ] Upravit nursery.html (přidat modal)
- [ ] Upravit tabulku nursery_plants
- [ ] Otestovat autocomplete
- [ ] Otestovat uložení rostliny s daty z katalogu

## 🎉 Hotovo!

Teď máš plně funkční katalog rostlin s autocomplete a automatickým vyplňováním botanických údajů!
