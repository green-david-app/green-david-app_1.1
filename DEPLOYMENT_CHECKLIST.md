# Deployment Checklist - Mobile UI na Render

## ✅ Před nasazením

### 1. Soubory a struktura
- [x] Všechny nové templates jsou v `templates/mobile/`
- [x] Všechny nové CSS soubory jsou v `static/css/`
- [x] Všechny nové JS soubory jsou v `static/js/`
- [x] Všechny nové Python moduly jsou v `app/utils/` a `config/`
- [x] `offline-queue.js` je vytvořen

### 2. Database Migrations
- [x] Migration v28 (Role Extension) - přidána
- [x] Migration v29 (UserSettings) - přidána
- [x] Migration v30 (UserDashboardLayout) - přidána
- [x] Migration v31 (ProcessedEvents) - přidána

### 3. Routes
- [x] `/mobile/today` - FIELD mode dashboard
- [x] `/mobile/dashboard` - FULL mode dashboard
- [x] `/mobile/edit-dashboard` - Widget editor
- [x] `/mobile/tasks` - Tasks page
- [x] `/mobile/photos` - Photos page
- [x] `/mobile/notifications` - Notifications page
- [x] `/mobile/demo` - Demo page

### 4. API Endpoints
- [x] Widget data endpoints (`/api/widgets/*`)
- [x] Quick actions endpoints (`/api/worklogs`, `/api/photos`, `/api/materials/use`, `/api/blockers`)
- [x] Offline queue endpoints (`/api/offline/queue`, `/api/offline/status`)
- [x] User settings endpoints (`/api/user/settings`, `/api/user/dashboard-layout`)

## 🔧 Konfigurace Render

### Environment Variables
Ujisti se, že jsou nastaveny:
- `SECRET_KEY` - pro Flask session (doporučeno vygenerovat nový)
- `DB_PATH` - cesta k databázi (volitelné, Render automaticky detekuje)
- `UPLOAD_DIR` - cesta pro uploady (default: `uploads`)

### Build Command
Render automaticky detekuje Flask aplikaci. Pokud potřebuješ custom build:
```bash
pip install -r requirements.txt
```

### Start Command
```bash
gunicorn main:app
```

Nebo pokud používáš `wsgi.py`:
```bash
gunicorn wsgi:app
```

## 📱 Testování po nasazení

### 1. Základní funkce
- [ ] Otevři `/mobile/today` - mělo by se zobrazit FIELD mode dashboard
- [ ] Otevři `/mobile/dashboard?mode=full` - mělo by se zobrazit FULL mode dashboard
- [ ] Zkontroluj, že se načítají CSS soubory (zkontroluj Network tab v DevTools)
- [ ] Zkontroluj, že se načítají JS soubory

### 2. Widget systém
- [ ] Otevři `/mobile/edit-dashboard` - měl by se zobrazit widget editor
- [ ] Zkus přidat/odebrat widgety
- [ ] Zkus změnit pořadí widgetů (drag & drop)
- [ ] Ulož změny a ověř, že se uložily

### 3. API Endpoints
Testuj pomocí curl nebo Postman:
```bash
# Widget data
curl https://your-app.onrender.com/api/widgets/current-job
curl https://your-app.onrender.com/api/widgets/my-tasks
curl https://your-app.onrender.com/api/widgets/notifications

# Quick actions (vyžaduje autentizaci)
curl -X POST https://your-app.onrender.com/api/worklogs \
  -H "Content-Type: application/json" \
  -H "Cookie: session=..." \
  -d '{"job_id": 1, "duration": 60}'
```

### 4. Mobile Mode Switch
- [ ] Přihlas se jako uživatel
- [ ] Zkus přepnout mezi FIELD a FULL mode
- [ ] Ověř, že se preference ukládají
- [ ] Ověř, že se preference načítají při příštím přihlášení

### 5. Offline Queue
- [ ] Otevři DevTools → Network → Offline
- [ ] Zkus vytvořit worklog (mělo by se přidat do queue)
- [ ] Zapni Online
- [ ] Ověř, že se queue synchronizovala

## 🐛 Časté problémy

### Problém: CSS/JS soubory se nenačítají
**Řešení:**
- Zkontroluj, že Flask má správně nastaven `static_folder`
- V `main.py` je `static_folder="."` což znamená root directory
- Statické soubory by měly být dostupné na `/static/...`

### Problém: Templates se nenačítají
**Řešení:**
- Zkontroluj, že všechny templates jsou v `templates/` adresáři
- Zkontroluj, že Flask má správně nastaven `template_folder` (default: `templates`)

### Problém: Database migrace se nespustí
**Řešení:**
- Zkontroluj logy na Render dashboardu
- Ověř, že `apply_migrations()` je volána při startu aplikace
- Zkontroluj, že databáze má správná oprávnění

### Problém: Uploads nefungují
**Řešení:**
- Zkontroluj, že `UPLOAD_DIR` existuje a má správná oprávnění
- Na Render může být potřeba použít persistent disk pro uploads
- Zkontroluj, že cesta k uploads je správně nastavena

## 📝 Poznámky

1. **Static Files**: Flask má `static_folder="."` což znamená, že statické soubory jsou v root adresáři. To funguje, protože všechny statické soubory jsou v `static/` adresáři a Flask je servuje přes `url_for('static', filename='...')`.

2. **Database**: Render automaticky detekuje persistent disk. Pokud máš persistent disk, použije `/persistent/app.db`, jinak `/tmp/app.db` (což je také persistent na Render).

3. **Uploads**: Pro produkci doporučuji použít cloud storage (S3, Cloudinary) místo lokálního filesystému. Pro teď můžeš použít persistent disk na Render.

4. **HTTPS**: Render automaticky poskytuje HTTPS, takže všechny API volání budou přes HTTPS.

5. **CORS**: Pokud potřebuješ CORS pro API, můžeš přidat Flask-CORS do `requirements.txt`.

## 🚀 Post-Deployment

Po úspěšném nasazení:
1. Otestuj všechny funkce na mobilním zařízení
2. Zkontroluj logy pro případné chyby
3. Ověř, že všechny migrace proběhly správně
4. Nastav monitoring a alerting (volitelné)

## 📞 Support

Pokud narazíš na problémy:
1. Zkontroluj Render logs
2. Zkontroluj browser console (F12)
3. Zkontroluj Network tab v DevTools
4. Ověř, že všechny soubory jsou správně commitnuté do Git
