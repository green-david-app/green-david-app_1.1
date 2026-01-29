#!/bin/bash
# 🔥 Automatická oprava katalogu rostlin

set -e  # Zastav při jakékoli chybě

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🔧 OPRAVA KATALOGU ROSTLIN"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# 1. Vyčisti starou tabulku
echo "🗑️  Mažu chybná data..."
python3 -c "import sqlite3; c=sqlite3.connect('app.db'); c.execute('DELETE FROM plant_catalog'); c.commit(); print(f'   ✅ Vymazáno: {c.execute(\"SELECT changes()\").fetchone()[0]} řádků')"

echo ""

# 2. Reimportuj s opraveným skriptem
echo "📥 Importuji správná data..."
python3 import_plant_catalog.py cenik_celorocni-pereny.docx app.db

echo ""

# 3. Ověř výsledky
echo "🔍 Ověřuji kvalitu dat..."
python3 << 'PYTHON'
import sqlite3
conn = sqlite3.connect('app.db')
cursor = conn.cursor()

# Celkový počet
cursor.execute("SELECT COUNT(*) FROM plant_catalog")
total = cursor.fetchone()[0]
print(f"   📊 Celkem rostlin: {total}")

# Zkontroluj špatné názvy
cursor.execute("""
    SELECT COUNT(*) FROM plant_catalog 
    WHERE latin_name LIKE '% - K%' 
       OR latin_name LIKE '%paznehtník%'
       OR latin_name LIKE '%oměj%'
       OR latin_name LIKE '%plazilka%'
""")
bad = cursor.fetchone()[0]

if bad > 0:
    print(f"   ❌ CHYBA: {bad} rostlin má chybné názvy!")
    cursor.execute("""
        SELECT latin_name FROM plant_catalog 
        WHERE latin_name LIKE '% - K%' 
        LIMIT 3
    """)
    for row in cursor.fetchall():
        print(f"      Příklad: {row[0]}")
    exit(1)
else:
    print(f"   ✅ Žádné chybné názvy")

# Ukázky
print("\n   📋 Ukázka rostlin:")
cursor.execute("SELECT latin_name, variety, container_size FROM plant_catalog LIMIT 5")
for row in cursor.fetchall():
    variety = f" '{row[1]}'" if row[1] else ""
    container = f" - {row[2]}" if row[2] else ""
    print(f"      {row[0]}{variety}{container}")

# Test vyhledávání
print("\n   🔍 Test vyhledávání:")
for q in ['aqui', 'lavand', 'acaena']:
    cursor.execute("SELECT COUNT(*) FROM plant_catalog WHERE latin_name LIKE ?", (f'%{q}%',))
    count = cursor.fetchone()[0]
    print(f"      '{q}' → {count} výsledků")

conn.close()
PYTHON

if [ $? -ne 0 ]; then
    echo ""
    echo "❌ OPRAVA SELHALA!"
    exit 1
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🎉 HOTOVO!"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "✅ Katalog byl úspěšně opraven"
echo ""
echo "🚀 Teď můžeš:"
echo "   1. Restartovat aplikaci:"
echo "      python3 main.py"
echo ""
echo "   2. Otevřít prohlížeč:"
echo "      http://127.0.0.1:5000/nursery.html"
echo ""
echo "   3. Vyzkoušet vyhledávání:"
echo "      Klikni 'Přidat rostlinu' a začni psát 'aqui' nebo 'lavand'"
echo ""
