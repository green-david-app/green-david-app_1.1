#!/bin/bash
# Green David App - Localhost Startup Script
# Pro Mac / Linux

echo "🚀 Spouštím Green David App..."
echo ""

# Kontrola Python verze
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 není nainstalován!"
    echo "   Nainstaluj Python3: https://www.python.org/downloads/"
    exit 1
fi

echo "✅ Python3 nalezen: $(python3 --version)"

# Kontrola Flask
if ! python3 -c "import flask" 2>/dev/null; then
    echo "📦 Flask není nainstalován, instaluji..."
    pip3 install flask --break-system-packages 2>/dev/null || pip3 install flask
fi

echo "✅ Flask nainstalován"
echo ""

# Nastavení proměnných
export ADMIN_EMAIL="admin@greendavid.local"
export ADMIN_PASSWORD="admin123"
export DB_PATH="./app.db"

echo "📊 Nastavení:"
echo "   Admin email: $ADMIN_EMAIL"
echo "   Admin heslo: $ADMIN_PASSWORD"
echo "   Databáze: $DB_PATH"
echo ""

# Kontrola existence databáze
if [ ! -f "$DB_PATH" ]; then
    echo "🆕 Vytvářím novou databázi..."
else
    echo "📁 Používám existující databázi: $DB_PATH"
    echo "   (Záloha: app.db.backup_$(date +%Y%m%d_%H%M%S))"
    cp app.db "app.db.backup_$(date +%Y%m%d_%H%M%S)"
fi

echo ""
echo "🌐 Server poběží na: http://127.0.0.1:5000"
echo "🔐 Přihlášení:"
echo "   Email: $ADMIN_EMAIL"
echo "   Heslo: $ADMIN_PASSWORD"
echo ""
echo "⚠️  Pro zastavení serveru zmáčkni CTRL+C"
echo ""
echo "──────────────────────────────────────────────────────────"
echo ""

# Spuštění
python3 main.py
