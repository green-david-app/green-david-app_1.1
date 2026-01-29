# 📦 OBSAH BALÍČKU - KATALOG ROSTLIN

## 📄 Soubory v tomto balíčku:

### 1. **README_PLANT_CATALOG.md** ⭐
   - Kompletní návod krok za krokem
   - Jak to funguje, jak nainstalovat, jak používat
   - **ZAČNI TADY!**

### 2. **install_plant_catalog.sh** 🚀
   - Automatický instalační skript
   - Spustí základní kroky (vytvoří tabulky, zkopíruje soubory)
   - Použití: `bash install_plant_catalog.sh`

### 3. **plant_catalog_migration.sql** 🗄️
   - SQL migrace pro vytvoření tabulky `plant_catalog`
   - Obsahuje:
     - Hlavní tabulku s botanickými údaji
     - Full-text search (FTS) pro rychlé vyhledávání
     - Triggery pro automatickou aktualizaci
   - Aplikace: `sqlite3 instance/green_david.db < plant_catalog_migration.sql`

### 4. **nursery_plants_migration.sql** 🗄️
   - SQL migrace pro rozšíření/vytvoření tabulky `nursery_plants`
   - Přidá botanické sloupce do existující tabulky
   - Nebo vytvoří novou kompletní tabulku
   - Aplikace: `sqlite3 instance/green_david.db < nursery_plants_migration.sql`

### 5. **import_plant_catalog.py** 📥
   - Python skript pro import dat z DOCX ceníku
   - Parsuje strukturu DOCX a načte všechny rostliny
   - Podporuje zkratky (A. → Aquilegia, atd.)
   - Použití: `python3 import_plant_catalog.py cenik.docx instance/green_david.db`

### 6. **plant_catalog_api.py** 🔌
   - API endpointy pro Flask aplikaci
   - Endpointy:
     - `/api/plant-catalog/search` - vyhledávání (autocomplete)
     - `/api/plant-catalog/<id>` - detail rostliny
     - `/api/plant-catalog/stats` - statistiky katalogu
     - `/api/plant-catalog/by-name` - hledání podle přesného názvu
   - **PŘIDEJ KÓD Z TOHOTO SOUBORU DO app.py**

### 7. **plant_catalog_autocomplete.js** ⌨️
   - JavaScript komponenta pro autocomplete
   - Funkce:
     - Real-time vyhledávání při psaní
     - Zobrazení výsledků s detaily
     - Klávesnice (šipky, Enter, Escape)
     - Automatické vyplnění formuláře
   - **ZKOPÍRUJ DO static/**

### 8. **plant_modal_example.html** 📝
   - Příklad HTML kódu pro modal "Přidat rostlinu"
   - Obsahuje:
     - Autocomplete input
     - Formulář s botanickými údaji
     - Formulář se školkařskými údaji
     - CSS styly
     - JavaScript pro obsluhu
   - **POUŽI JAKO ŠABLONU PRO nursery.html**

---

## 🔧 RYCHLÝ START:

1. **Přečti si README_PLANT_CATALOG.md**
2. **Zkopíruj DOCX do instance/**
   ```bash
   cp cenik_celorocni-pereny.docx ~/Green-David-App/instance/
   ```
3. **Spusť instalační skript:**
   ```bash
   cd ~/Green-David-App
   bash install_plant_catalog.sh
   ```
4. **Přidej API endpointy do app.py**
   (zkopíruj z plant_catalog_api.py)

5. **Uprav nursery.html**
   (použij plant_modal_example.html jako šablonu)

6. **Restartuj aplikaci a vyzkoušej!**
   ```bash
   sudo systemctl restart greendavid
   ```

---

## 🎯 Co to přináší?

### ✅ Pro tebe:
- **Rychlejší zadávání rostlin** - začneš psát název, vybereš z katalogu
- **Automatické vyplnění údajů** - barva květu, výška, nároky...
- **Konzistentní data** - všechny rostliny mají stejné údaje
- **Databáze znalostí** - botanické údaje ke každé rostlině

### 📊 Statistiky:
Z ceníku se naimportuje **cca 800-1000 rostlin** s údaji:
- Latinský název + odrůda
- Barva květu, doba květu
- Výška, nároky na světlo
- Stanoviště, počet ks/m²
- Zona mrazuvzdornost
- Poznámky a specifikace

---

## 📞 Potřebuješ pomoct?

Pokud něco nefunguje:
1. Zkontroluj README_PLANT_CATALOG.md sekci "Možné problémy"
2. Otevři Chrome DevTools (F12) a podívej se na chyby v Console
3. Zkontroluj, že všechny endpointy v app.py jsou správně přidané

---

## 💡 Další vylepšení (volitelné):

- **Obrázky rostlin** - přidat sloupec `image_url`
- **České názvy** - přidat `czech_name` pro vyhledávání
- **Kategorie** - přidat `category` (trvalky, traviny...)
- **Export ceníku** - generovat vlastní ceník z databáze
- **QR kódy** - na štítky rostlin
- **Statistiky** - kolik které rostliny je v pěstování

---

Hodně štěstí s implementací! 🌿🚀
