# 🔧 Opravy pro Render.com deployment

## Problém
Aplikace na Render.com nefungovala správně - chyběly routy pro nové HTML soubory a statické JS soubory.

## Opravy v main.py

### 1. Přidány routy pro nové HTML soubory
```python
@app.route("/jobs.html")
def page_jobs():
    return send_from_directory(".", "jobs.html")

@app.route("/tasks.html")
def page_tasks():
    return send_from_directory(".", "tasks.html")

@app.route("/employees.html")
def page_employees():
    return send_from_directory(".", "employees.html")

@app.route("/calendar.html")
def page_calendar():
    return send_from_directory(".", "calendar.html")

@app.route("/settings.html")
def page_settings():
    return send_from_directory(".", "settings.html")

@app.route("/warehouse.html")
def page_warehouse():
    return send_from_directory(".", "warehouse.html")

@app.route("/finance.html")
def page_finance():
    return send_from_directory(".", "finance.html")

@app.route("/documents.html")
def page_documents():
    return send_from_directory(".", "documents.html")

@app.route("/reports.html")
def page_reports():
    return send_from_directory(".", "reports.html")
```

### 2. Přidána routa pro statické soubory
```python
@app.route("/static/<path:filename>")
def static_files(filename):
    """Serve static files from static/ directory"""
    return send_from_directory("static", filename)
```

## Ověření

Po nasazení by měly fungovat:
- ✅ `/jobs.html` - Kanban board zakázek
- ✅ `/tasks.html` - TODO systém
- ✅ `/employees.html` - Grid zaměstnanců
- ✅ `/static/toast.js` - Toast notifikace
- ✅ `/static/loading.js` - Loading overlay
- ✅ `/static/global-search.js` - Globální vyhledávání
- ✅ `/static/keyboard-shortcuts.js` - Klávesové zkratky

## Testování

1. Otevři aplikaci na Render.com
2. Zkontroluj Console (F12) - neměly by být 404 chyby
3. Otestuj všechny stránky:
   - `/jobs.html`
   - `/tasks.html`
   - `/employees.html`
4. Zkontroluj, že fungují:
   - Toast notifikace
   - Globální vyhledávání (Cmd/Ctrl+K)
   - Klávesové zkratky

## Pokud stále nefunguje

1. Zkontroluj logy na Render.com
2. Otevři DevTools → Network tab
3. Podívej se, které soubory se nenačítají (404)
4. Zkontroluj cesty v HTML souborech

