#!/bin/bash
# Quick Install Script pro Plant Catalog System
# Použití: ./install_plant_catalog.sh

echo "🌿 INSTALACE KATALOGU ROSTLIN 🌿"
echo "================================"
echo ""

# Kontrola, že jsme ve správné složce
if [ ! -f "app.py" ]; then
    echo "❌ Chyba: Nejsi ve složce Green-David-App"
    echo "   Přejdi do složky aplikace: cd ~/Green-David-App"
    exit 1
fi

echo "✓ Detekována složka aplikace"
echo ""

# 1. Aplikuj SQL migraci
echo "📊 1. Vytvářím tabulku plant_catalog..."
if sqlite3 instance/green_david.db < plant_catalog_migration.sql; then
    echo "   ✓ Tabulka vytvořena"
else
    echo "   ⚠ Možná už existuje"
fi
echo ""

# 2. Zkontroluj python-docx
echo "📦 2. Kontroluji python-docx..."
if python3 -c "import docx" 2>/dev/null; then
    echo "   ✓ python-docx je nainstalovaný"
else
    echo "   ⚠ Instaluji python-docx..."
    pip3 install python-docx --break-system-packages
fi
echo ""

# 3. Import dat (pokud existuje DOCX)
if [ -f "instance/cenik_celorocni-pereny.docx" ]; then
    echo "📥 3. Importuji data z ceníku..."
    python3 import_plant_catalog.py instance/cenik_celorocni-pereny.docx instance/green_david.db
    echo ""
else
    echo "⏭️  3. Přeskakuji import - soubor cenik_celorocni-pereny.docx nenalezen"
    echo "   📌 Nahraj DOCX do instance/ a spusť:"
    echo "      python3 import_plant_catalog.py instance/cenik_celorocni-pereny.docx instance/green_david.db"
    echo ""
fi

# 4. Zkopíruj JavaScript
echo "📂 4. Kopíruji JavaScript soubor..."
if cp plant_catalog_autocomplete.js static/; then
    echo "   ✓ Zkopírováno do static/"
else
    echo "   ❌ Chyba při kopírování"
    exit 1
fi
echo ""

# 5. Info o dalších krocích
echo "✅ ZÁKLADNÍ INSTALACE DOKONČENA!"
echo ""
echo "📋 ZBÝVAJÍCÍ KROKY (manuálně):"
echo "   1. Přidej API endpointy do app.py"
echo "      (viz plant_catalog_api.py)"
echo ""
echo "   2. Uprav nursery.html:"
echo "      - Přidej <script src='/static/plant_catalog_autocomplete.js'></script>"
echo "      - Přidej modal pro přidání rostliny (viz plant_modal_example.html)"
echo ""
echo "   3. Restartuj aplikaci:"
echo "      sudo systemctl restart greendavid"
echo ""
echo "   4. Otevři aplikaci a vyzkoušej autocomplete!"
echo ""
echo "📖 Kompletní návod najdeš v README_PLANT_CATALOG.md"
echo ""
