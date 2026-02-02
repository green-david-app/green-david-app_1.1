# Current State Map - Green David App

## Layout
- **Hlavní layout**: `templates/layout.html`
  - Základní HTML struktura s `<main class="container">`
  - Viewport meta tag: `<meta name="viewport" content="width=device-width, initial-scale=1"/>`
  - Footer: `<footer class="footer">`
  
- **Header komponenta**: `static/app-header.js`
  - Dynamicky generovaný header třídou `AppHeader`
  - Vložen do `<div id="app-header"></div>`
  - Obsahuje: logo, vyhledávání, AI operátor, úkoly, notifikace, nastavení, logout
  - Responsivní: na mobilu se skrývá text, zmenšuje se výška
  
- **Bottom nav**: `static/bottom-nav.js`
  - Univerzální bottom navigation pro celou aplikaci
  - Vložena do `<div id="bottom-nav-container"></div>`
  - Položky: Home, Jobs, Timesheets, Calendar, Reports, More (dropdown menu)
  - Aktivní stav se detekuje podle aktuální cesty
  - CSS: `.bottom-nav` s pozicí `bottom: 8px` na mobilu

## Mobilní detekce
- **Metoda**: CSS media queries
- **Breakpointy**: 
  - `@media (max-width: 768px)` v `static/style.css` (řádek 1316)
  - Žádná JavaScript detekce mobilního zařízení
  - Viewport meta tag je nastavený správně
- **Mobilní úpravy**:
  - Zmenšený padding body (72px top, 80px bottom)
  - Kompaktnější header (52px výška)
  - Skryté vyhledávání na mobilu
  - Bottom nav na spodku obrazovky

## Auth & Role
- **User model**: Tabulka `users` v `main.py` (řádek 1792)
  ```sql
  CREATE TABLE IF NOT EXISTS users (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      email TEXT UNIQUE NOT NULL,
      name TEXT NOT NULL,
      role TEXT NOT NULL DEFAULT 'worker' 
          CHECK(role IN ('owner','manager','team_lead','worker','admin')),
      password_hash TEXT NOT NULL,
      active INTEGER NOT NULL DEFAULT 1,
      created_at TEXT NOT NULL DEFAULT (datetime('now')),
      manager_id INTEGER NULL
  );
  ```
  
- **Role field**: `role` v tabulce `users`
- **Současné role**: 
  - `owner` - vlastník
  - `manager` - manažer
  - `team_lead` - vedoucí týmu
  - `worker` - pracovník
  - `admin` - administrátor
  
- **Session storage**: Role je uložena v session jako `user_role`
- **JavaScript helpers**: V `templates/layout.html` (řádek 164-193)
  - `window.currentUser.role`
  - `window.hasRole(...roles)`
  - `window.isOwner()`
  - `window.isManager()`
  - `window.canApprove()`
  - `window.canManageEmployees()`

## Routes
- **Zakázky**: 
  - Route: `/jobs.html`
  - Soubor: `main.py` (řádek ~1491)
  - Template: `jobs.html` (v rootu)
  
- **Výkazy**: 
  - Route: `/timesheets.html`
  - API: `/api/timesheets` (GET, POST, PATCH, DELETE)
  - Soubor: `main.py` (řádek 6072, 4844)
  - Template: `templates/timesheets.html`
  
- **Úkoly**: 
  - Route: `/tasks.html`
  - API: `/api/tasks` (GET, POST, PATCH, PUT, DELETE)
  - Soubor: `main.py` (řádek 6081, 4404)
  - Template: `tasks.html` (v rootu)
  
- **Sklad**: 
  - Route: `/warehouse.html`
  - API: `/gd/api/warehouse/items` (GET)
  - Soubor: `main.py` (řádek 6102, 7326)
  - Template: `warehouse.html` (v rootu)
  
- **Notifikace**: 
  - Route: `/notifications.html` (pravděpodobně)
  - API: `/api/notifications` (GET, PATCH, DELETE)
  - Soubor: `main.py` (řádek 2660)
  - Template: `notifications.html` (v rootu)

- **Žádné specifické mobilní routes** - vše sdílené mezi desktop a mobile

## Data Model
- **ORM**: SQLite s přímými SQL dotazy (ne SQLAlchemy)
- **Migrace**: Vlastní migrační systém v `main.py`
  - Funkce: `apply_migrations()` (řádek 274)
  - Tabulka: `schema_migrations` pro tracking verzí
  - Migrace jsou aplikovány při startu aplikace (`@app.before_request`)
  
- **Hlavní tabulky**:
  - `users` - uživatelské účty s rolemi
  - `employees` - zaměstnanci (propojeno s `users` přes `user_id`)
  - `jobs` - zakázky
  - `tasks` - úkoly
  - `warehouse_items` - skladové položky
  - `notifications` - notifikace
  - `timesheets` - výkazy hodin
  - `task_events` - event-driven systém pro úkoly
  - `task_dependencies` - závislosti mezi úkoly
  - `audit_log` - audit log

- **Vztahy**:
  - `employees.user_id` → `users.id` (1:1)
  - `tasks.job_id` → `jobs.id` (N:1)
  - `tasks.assigned_employee_id` → `employees.id` (N:1)
  - `notifications.user_id` → `users.id` (N:1)

## Struktura projektu
```
green-david-WORK/
├── main.py                    # Hlavní Flask aplikace + routes + migrace
├── templates/
│   ├── layout.html            # Základní layout template
│   └── timesheets.html        # Template pro výkazy
├── static/
│   ├── style.css             # Hlavní CSS (s media queries)
│   ├── css/
│   │   └── app.css           # Dodatečné CSS
│   ├── app-header.js         # Header komponenta
│   └── bottom-nav.js         # Bottom navigation
├── app/
│   ├── __init__.py
│   ├── models.py
│   ├── api.py
│   ├── middleware/
│   │   └── audit.py
│   └── routes/
│       └── api/              # API routes
└── [standalone HTML files]   # jobs.html, tasks.html, warehouse.html, etc.
```

## Pozorování
1. **Žádné mobilní-specifické routes** - vše je sdílené
2. **CSS-only responsive design** - žádná JS detekce zařízení
3. **Role systém existuje**, ale není plně využit pro UI filtrování
4. **Bottom nav je univerzální** - stejná pro všechny stránky
5. **Header je dynamický** - generuje se JS, obsahuje notifikace a úkoly
6. **Offline support**: Existuje v `task_events` (pole `occurred_offline`, `synced_at`), ale není implementován frontend queue systém
7. **Widget systém neexistuje** - žádné konfigurovatelné dashboardy

## Návrh struktury nových souborů

```
/static/js/
├── mode.js                   # FIELD/FULL přepínání
├── widgets.js                # Widget registry a rendering
├── offline-queue.js          # Offline event queue
└── api-wrapper.js            # API fetch s offline fallbackem

/templates/
├── layouts/
│   ├── layout_mobile_field.html
│   └── layout_mobile_full.html
└── widgets/
    ├── current_job.html
    ├── quick_log.html
    ├── my_tasks.html
    ├── add_photo.html
    ├── material_quick.html
    ├── report_blocker.html
    ├── offline_status.html
    ├── notifications.html
    ├── jobs_risk.html
    ├── overdue_jobs.html
    ├── team_load.html
    ├── stock_alerts.html
    └── budget_burn.html

/templates/mobile/
├── dashboard.html            # Widget dashboard
├── today.html               # Today screen (field mode)
├── edit_dashboard.html      # Widget editor
└── queue.html               # Offline queue viewer

/app/utils/
└── permissions.py            # RBAC helper funkce

/app/utils/
└── widgets.py               # Widget rendering logika

/config/
└── widgets.py                # Widget registry + role defaults

/app/models.py                # Rozšíření: UserSettings, UserDashboardLayout, ProcessedEvent
```

---

**Datum auditu**: 2025-01-XX
**Status**: ✅ Kompletní audit dokončen
