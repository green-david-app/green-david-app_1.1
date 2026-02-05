#!/bin/bash
# Instalační script pro Nursery modul
# Spustit: bash install_nursery.sh

echo "🌸 Installing Nursery Module..."
echo ""

# Kontrola existence databáze
if [ ! -f "app.db" ]; then
    echo "❌ Soubor app.db nebyl nalezen!"
    echo "   Spusť nejdřív hlavní aplikaci pro vytvoření databáze."
    exit 1
fi

echo "✅ Databáze nalezena"
echo ""

# Kontrola existence tabulek
echo "Kontroluji strukturu databáze..."
python3 << 'CHECKPY'
import sqlite3
conn = sqlite3.connect('app.db')
cursor = conn.cursor()

# Zkontroluj existující tabulky
cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE '%nursery%'")
tables = cursor.fetchall()

if len(tables) >= 3:
    print("✅ Nursery tabulky již existují")
    print(f"   Nalezené tabulky: {', '.join([t[0] for t in tables])}")
else:
    print("❌ Nursery tabulky neexistují")
    print("   Je potřeba je vytvořit")
    
conn.close()
CHECKPY

echo ""
read -p "Chceš naplnit databázi testovacími daty? (ano/ne): " LOAD_DATA

if [ "$LOAD_DATA" = "ano" ] || [ "$LOAD_DATA" = "a" ]; then
    echo ""
    echo "📦 Načítám testovací data..."
    python3 << 'LOADPY'
import sqlite3
conn = sqlite3.connect('app.db')

# Načti SQL soubor
with open('nursery_test_data.sql', 'r', encoding='utf-8') as f:
    sql_script = f.read()

try:
    conn.executescript(sql_script)
    conn.commit()
    print("✅ Testovací data úspěšně načtena")
except Exception as e:
    print(f"❌ Chyba při načítání dat: {e}")
finally:
    conn.close()
LOADPY
fi

echo ""
echo "✅ Instalace dokončena!"
echo ""
echo "📋 Další kroky:"
echo "   1. Restartuj Flask aplikaci"
echo "   2. Otevři http://localhost:5005/nursery"
echo "   3. Začni přidávat rostliny"
echo ""
echo "📚 Dokumentace: NURSERY_README.md"
echo ""
