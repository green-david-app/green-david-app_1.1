# 🌿 KATALOG ROSTLIN - ZMĚNY V APLIKACI

## 📅 Datum: 29. ledna 2026

## ✨ Co je nového:

### 1. **Katalog rostlin s botanickými údaji**
   - Databázová tabulka `plant_catalog` pro uložení cca 800-1000 rostlin z ceníku
   - Full-text search (FTS) pro rychlé vyhledávání
   - Import dat z DOCX souboru

### 2. **Autocomplete při přidávání rostlin**
   - Začneš psát název → zobrazí se seznam z katalogu
   - Klikneš na rostlinu → automaticky se vyplní všechny botanické údaje
   - Nebo vytvoříš rostlinu ručně s prázdným formulářem

### 3. **Nové API endpointy**
   - `/api/plant-catalog/search` - vyhledávání (autocomplete)
   - `/api/plant-catalog/<id>` - detail rostliny
   - `/api/plant-catalog/stats` - statistiky katalogu
   - `/api/plant-catalog/by-name` - hledání podle přesného názvu

### 4. **Nový modal pro přidání rostliny**
   - Vyhledávání v katalogu s autocomplete
   - Formulář s botanickými údaji (barva květu, výška, nároky...)
   - Formulář se školkařskými údaji (počet, umístění, cena...)
   - Responzivní design pro mobily

---

## 📂 Nové soubory:

### SQL migrace:
- `plant_catalog_migration.sql` - Tabulka pro katalog rostlin
- `nursery_plants_migration.sql` - Rozšíření tabulky školky

### Python skripty:
- `import_plant_catalog.py` - Import dat z DOCX ceníku

### JavaScript:
- `static/plant_catalog_autocomplete.js` - Autocomplete komponenta

### Dokumentace:
- `README_PLANT_CATALOG.md` - Kompletní návod
- `PLANT_CATALOG_PREHLED.md` - Rychlý přehled
- `install_plant_catalog.sh` - Instalační skript

### Data:
- `cenik_celorocni-pereny.docx` - Ceník k importu

---

## 🔧 Změněné soubory:

### `main.py`
- ➕ Přidány 4 nové API endpointy pro katalog rostlin
- Umístění: před `if __name__ == "__main__"` (řádek ~5300)

### `nursery.html`
- ➕ Přidán script `plant_catalog_autocomplete.js` do hlavičky
- ➕ Přidán kompletní modal pro přidání/editaci rostliny
- ➕ Přidány JavaScript funkce pro autocomplete a uložení
- ➕ Přidány CSS styly pro formulář
- ➕ Přidáno tlačítko "Přidat rostlinu" v sekci Rostliny

---

## 🚀 Jak to použít:

### 1. Aplikuj SQL migrace:
```bash
sqlite3 app.db < plant_catalog_migration.sql
sqlite3 app.db < nursery_plants_migration.sql
```

### 2. Importuj data z ceníku:
```bash
pip3 install python-docx --break-system-packages
python3 import_plant_catalog.py cenik_celorocni-pereny.docx app.db
```

### 3. Restartuj aplikaci:
```bash
sudo systemctl restart greendavid
```

### 4. Vyzkoušej!
1. Otevři aplikaci → Sekce Školka
2. Klikni na tab "Rostliny"
3. Klikni "Přidat rostlinu"
4. Začni psát do pole "Vyhledat v katalogu" např. "aqui"
5. Vyber rostlinu → automaticky se vyplní údaje
6. Doplň školkařské údaje (počet, umístění...)
7. Ulož

---

## 💡 Co to přináší:

✅ **Rychlejší zadávání** - autocomplete místo ručního psaní  
✅ **Konzistentní data** - všechny rostliny mají stejné botanické údaje  
✅ **Databáze znalostí** - info o barvě květu, výšce, nárocích...  
✅ **Profesionální vzhled** - jako mají velké školky  
✅ **Úspora času** - nemusíš pamatovat všechny údaje  

---

## 🐛 Známé omezení:

⚠️ **API endpoint pro uložení rostliny není implementován**  
   - Modal funguje, autocomplete funguje
   - Ale uložení rostliny zatím jen loguje do konzole
   - V další verzi přidáme endpoint `/api/nursery/plants`

---

## 📖 Další informace:

Kompletní dokumentaci najdeš v:
- `README_PLANT_CATALOG.md` - Detailní návod
- `PLANT_CATALOG_PREHLED.md` - Rychlý přehled

---

## 🎯 Co dál:

1. **Implementovat API endpoint** pro uložení rostliny do databáze
2. **Implementovat seznam rostlin** v sekci Rostliny
3. **Přidat editaci** existujících rostlin
4. **Přidat filtry** (podle stavu, umístění, odrůdy...)
5. **Přidat export** do CSV/PDF
6. **Přidat obrázky rostlin** do katalogu
7. **Přidat české názvy** pro lepší vyhledávání

---

Vytvořil: Claude (Anthropic)  
Datum: 29. ledna 2026  
Pro: David @ Green David s.r.o.
