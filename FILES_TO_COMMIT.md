# Soubory k commitnutí do Git repozitáře

## 📝 Nové soubory (vytvořené)

### Konfigurace
- `config/permissions.py` - RBAC permission map
- `config/widgets.py` - Widget registry a role defaults
- `config/__init__.py` - Python package init

### Utility moduly
- `app/utils/permissions.py` - RBAC helper funkce a dekorátory
- `app/utils/mobile_mode.py` - Mobile mode detection a management
- `app/utils/widgets.py` - Widget system rendering a filtrování
- `app/utils/__init__.py` - Python package init

### Templates - Mobile layouts
- `templates/layouts/layout_mobile_field.html` - FIELD mode layout
- `templates/layouts/layout_mobile_full.html` - FULL mode layout

### Templates - Mobile stránky
- `templates/mobile/dashboard.html` - Mobile dashboard
- `templates/mobile/edit_dashboard.html` - Widget editor
- `templates/mobile/tasks.html` - Tasks stránka
- `templates/mobile/photos.html` - Photos stránka
- `templates/mobile/notifications.html` - Notifications stránka
- `templates/mobile/queue.html` - Queue stránka

### Templates - Widgety
- `templates/widgets/current_job.html` - Aktuální zakázka widget
- `templates/widgets/quick_log.html` - Quick log widget
- `templates/widgets/my_tasks.html` - Moje úkoly widget
- `templates/widgets/add_photo.html` - Přidat foto widget
- `templates/widgets/material_quick.html` - Výdej materiálu widget
- `templates/widgets/report_blocker.html` - Nahlásit problém widget
- `templates/widgets/offline_status.html` - Offline status widget
- `templates/widgets/notifications.html` - Notifications widget
- `templates/widgets/jobs_risk.html` - Rizikové zakázky widget
- `templates/widgets/overdue_jobs.html` - Zpožděné zakázky widget
- `templates/widgets/team_load.html` - Vytížení týmu widget
- `templates/widgets/stock_alerts.html` - Skladové výstrahy widget
- `templates/widgets/budget_burn.html` - Čerpání rozpočtu widget

### JavaScript
- `static/js/mode.js` - Mobile mode switch
- `static/js/widgets.js` - Widget editor drag & drop
- `static/js/offline-queue.js` - Offline queue manager

### CSS
- `static/css/mobile_field.css` - FIELD mode styly
- `static/css/mobile_full.css` - FULL mode styly
- `static/css/widgets.css` - Widget system styly

### Demo a dokumentace
- `mobile-demo.html` - Demo index stránka
- `MOBILE_UI_LINKS.md` - Funkční linky na mobile UI
- `ROUTES_API_SUMMARY.md` - Souhrn routes a API endpoints
- `DEPLOYMENT_CHECKLIST.md` - Checklist pro nasazení
- `MOBILE_UI_COMPLETION.md` - Dokončení implementace
- `MOBILE_SYSTEM_AUDIT.md` - Audit mobile systému
- `FILES_TO_COMMIT.md` - Tento soubor

## 🔄 Změněné soubory (upravené)

### Hlavní aplikace
- `main.py` - Přidány:
  - Migrace v28 (Role Extension)
  - Migrace v29 (UserSettings)
  - Migrace v30 (UserDashboardLayout)
  - Migrace v31 (ProcessedEvents)
  - Mobile routes (`/mobile/today`, `/mobile/dashboard`, `/mobile/queue`, atd.)
  - Widget API endpoints (`/api/widgets/*`)
  - Quick action API endpoints (`/api/worklogs`, `/api/photos`, `/api/materials/use`, `/api/blockers`)
  - Offline queue API endpoints (`/api/offline/queue`, `/api/offline/status`)
  - RBAC kontroly na endpoints
  - Template filter `event_type_label`
  - Cookie backup v `/api/user/settings`
  - Oprava "undefined" v stock alerts (COALESCE)

### Templates (pokud byly změněny)
- `templates/timesheets.html` - Možná přidána testovací sekce pro oprávnění (může být odstraněna)

## 📋 Doporučený commit postup

### 1. Commit - Konfigurace a utility
```bash
git add config/ app/utils/
git commit -m "feat: Přidán RBAC systém a widget registry

- RBAC permission map (config/permissions.py)
- Widget registry s role defaults (config/widgets.py)
- Mobile mode detection (app/utils/mobile_mode.py)
- Widget system helpers (app/utils/widgets.py)
- RBAC dekorátory (app/utils/permissions.py)"
```

### 2. Commit - Templates
```bash
git add templates/layouts/ templates/mobile/ templates/widgets/
git commit -m "feat: Přidány mobile UI templates

- FIELD a FULL mode layouts
- Mobile stránky (dashboard, tasks, photos, notifications, queue)
- Widget templates (13 widgetů)"
```

### 3. Commit - Frontend assets
```bash
git add static/js/mode.js static/js/widgets.js static/js/offline-queue.js
git add static/css/mobile_field.css static/css/mobile_full.css static/css/widgets.css
git commit -m "feat: Přidány JavaScript a CSS pro mobile UI

- Mode switch (mode.js)
- Widget editor (widgets.js)
- Offline queue manager (offline-queue.js)
- Mobile styly (mobile_field.css, mobile_full.css, widgets.css)"
```

### 4. Commit - Backend routes a API
```bash
git add main.py
git commit -m "feat: Přidány mobile routes a API endpoints

- Mobile routes (/mobile/today, /mobile/dashboard, /mobile/queue, atd.)
- Widget API endpoints (/api/widgets/*)
- Quick action endpoints (/api/worklogs, /api/photos, /api/materials/use, /api/blockers)
- Offline queue endpoints (/api/offline/*)
- RBAC kontroly na všechny endpoints
- Database migrace v28-v31
- Oprava 'undefined' v stock alerts"
```

### 5. Commit - Demo a dokumentace
```bash
git add mobile-demo.html *.md
git commit -m "docs: Přidána dokumentace a demo stránka

- Mobile UI demo (mobile-demo.html)
- API dokumentace (ROUTES_API_SUMMARY.md)
- Deployment checklist (DEPLOYMENT_CHECKLIST.md)
- Audit report (MOBILE_SYSTEM_AUDIT.md)"
```

## ⚠️ Poznámky

1. **`templates/timesheets.html`** - Pokud obsahuje testovací sekci pro oprávnění, může být odstraněna před commitem
2. **`.gitignore`** - Zkontroluj, že neignoruješ důležité soubory (např. `config/`, `app/utils/`)
3. **Database** - Migrace se spustí automaticky při prvním spuštění aplikace
4. **Dependencies** - Žádné nové Python balíčky nebyly přidány (pouze Flask standard)

## 🔍 Kontrola před commitem

```bash
# Zkontroluj status
git status

# Zkontroluj změny v hlavních souborech
git diff main.py | head -100

# Zkontroluj, že všechny nové soubory jsou přidány
git ls-files --others --exclude-standard
```

## 📦 Celkový počet souborů

- **Nové soubory**: ~40 souborů
- **Změněné soubory**: 1 soubor (`main.py`)
- **Celkem**: ~41 souborů
