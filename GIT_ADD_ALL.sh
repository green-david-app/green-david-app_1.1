#!/bin/bash
# Přidá všechny soubory mobile UI systému do Git

echo "Přidávám konfiguraci..."
git add config/__init__.py config/permissions.py config/widgets.py

echo "Přidávám utility moduly..."
git add app/utils/__init__.py app/utils/permissions.py app/utils/mobile_mode.py app/utils/widgets.py

echo "Přidávám templates..."
git add templates/layouts/layout_mobile_*.html
git add templates/mobile/*.html
git add templates/widgets/*.html

echo "Přidávám JavaScript..."
git add static/js/mode.js static/js/widgets.js static/js/offline-queue.js

echo "Přidávám CSS..."
git add static/css/mobile_field.css static/css/mobile_full.css static/css/widgets.css

echo "Přidávám demo..."
git add mobile-demo.html

echo "Přidávám hlavní soubor..."
git add main.py

echo "Přidávám dokumentaci..."
git add *.md

echo "✅ Hotovo! Zkontroluj s 'git status'"
