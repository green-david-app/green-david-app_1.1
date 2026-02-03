# Git Commit - Mobile UI Systém

## 🚀 Rychlý commit (vše najednou)

```bash
# Přidej všechny nové soubory mobile UI
git add config/ app/utils/permissions.py app/utils/mobile_mode.py app/utils/widgets.py app/utils/__init__.py
git add templates/layouts/ templates/mobile/ templates/widgets/
git add static/js/mode.js static/js/widgets.js static/js/offline-queue.js
git add static/css/mobile_field.css static/css/mobile_full.css static/css/widgets.css
git add mobile-demo.html
git add main.py

# Přidej dokumentaci (volitelné)
git add *.md

# Commit
git commit -m "feat: Mobile UI systém - FIELD/FULL mode, widgety, RBAC

- Přidán RBAC systém s permission map
- Widget registry s 13 widgety
- Mobile mode switch (FIELD/FULL)
- Mobile routes (/mobile/today, /mobile/dashboard, /mobile/queue)
- Widget API endpoints (/api/widgets/*)
- Quick action endpoints (/api/worklogs, /api/photos, /api/materials/use, /api/blockers)
- Offline queue support
- Database migrace v28-v31
- Oprava 'undefined' v stock alerts"
```

## 📋 Detailní seznam souborů

### Nové soubory k přidání:

```bash
# Konfigurace
git add config/__init__.py
git add config/permissions.py
git add config/widgets.py

# Utility moduly
git add app/utils/__init__.py
git add app/utils/permissions.py
git add app/utils/mobile_mode.py
git add app/utils/widgets.py

# Templates - Layouts
git add templates/layouts/layout_mobile_field.html
git add templates/layouts/layout_mobile_full.html

# Templates - Mobile stránky
git add templates/mobile/dashboard.html
git add templates/mobile/edit_dashboard.html
git add templates/mobile/tasks.html
git add templates/mobile/photos.html
git add templates/mobile/notifications.html
git add templates/mobile/queue.html

# Templates - Widgety
git add templates/widgets/current_job.html
git add templates/widgets/quick_log.html
git add templates/widgets/my_tasks.html
git add templates/widgets/add_photo.html
git add templates/widgets/material_quick.html
git add templates/widgets/report_blocker.html
git add templates/widgets/offline_status.html
git add templates/widgets/notifications.html
git add templates/widgets/jobs_risk.html
git add templates/widgets/overdue_jobs.html
git add templates/widgets/team_load.html
git add templates/widgets/stock_alerts.html
git add templates/widgets/budget_burn.html

# JavaScript
git add static/js/mode.js
git add static/js/widgets.js
git add static/js/offline-queue.js

# CSS
git add static/css/mobile_field.css
git add static/css/mobile_full.css
git add static/css/widgets.css

# Demo
git add mobile-demo.html

# Hlavní soubor (změněný)
git add main.py

# Dokumentace (volitelné)
git add MOBILE_SYSTEM_AUDIT.md
git add ROUTES_API_SUMMARY.md
git add DEPLOYMENT_CHECKLIST.md
git add MOBILE_UI_LINKS.md
git add FILES_TO_COMMIT.md
git add GIT_COMMIT_COMMANDS.md
```

## ⚠️ Co NEPŘIDÁVAT

Tyto soubory jsou buď dočasné nebo nepatří do repozitáře:

```bash
# Databáze (lokální)
app.db
app.db-shm
app.db-wal

# Systémové soubory
.DS_Store

# Dočasné skripty (pokud nejsou potřeba)
*.py (kromě těch v config/ a app/utils/)
*.sql (migrace jsou v main.py)
```

## 🔍 Kontrola před push

```bash
# Zkontroluj, co bude commitnuto
git status

# Zkontroluj změny v main.py
git diff main.py | head -200

# Zkontroluj, že všechny důležité soubory jsou přidány
git ls-files | grep -E "(config/|app/utils/|templates/mobile|templates/widgets|static/js/mode|static/css/mobile)"
```

## 📤 Push do repozitáře

```bash
# Push do hlavní větve (nebo vytvoř PR)
git push origin main

# Nebo push do nové větve
git checkout -b feature/mobile-ui
git push origin feature/mobile-ui
```

## ✅ Po push na Render

1. Render automaticky detekuje změny
2. Spustí build s `pip install -r requirements.txt`
3. Spustí aplikaci s `gunicorn main:app`
4. Migrace se spustí automaticky při prvním requestu
5. Otevři `/mobile/today` nebo `/mobile/dashboard` pro testování
