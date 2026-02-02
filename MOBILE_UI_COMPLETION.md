# Mobile UI - Dokončení implementace

## ✅ Dokončeno

### 1. RBAC Dekorátory
- ✅ Upraveny RBAC dekorátory v `app/utils/permissions.py` pro kompatibilitu s existujícím auth systémem
- ✅ Přidány RBAC kontroly na všechny widget endpoints:
  - `/api/widgets/jobs-risk` → `view_reports`
  - `/api/widgets/overdue-jobs` → `view_reports`
  - `/api/widgets/team-load` → `assign_people`
  - `/api/widgets/stock-alerts` → `log_material`
  - `/api/widgets/budget-burn` → `view_finance`
- ✅ Přidány RBAC kontroly na všechny quick action endpoints:
  - `/api/worklogs` → `log_work`
  - `/api/photos` → `add_photo`
  - `/api/materials/use` → `log_material`
  - `/api/blockers` → `create_blocker`

## 🔄 Potřeba dokončit

### 2. Mode Switch Endpoint
Endpoint `/api/user/settings` už existuje, ale potřebuje úpravy:

**Současný stav:** Endpoint existuje v `main.py` kolem řádku 14133

**Potřebné úpravy:**
1. Přidat cookie backup pro rychlý přístup
2. Zajistit, že `get_mobile_mode()` používá DB preference → cookie → auto podle role

### 3. Queue Stránka
**Chybí:** Route `/mobile/queue` a template

**Potřebné:**
1. Vytvořit route `/mobile/queue` v `main.py`
2. Vytvořit template `templates/mobile/queue.html`
3. Přidat JavaScript pro zobrazení queue z localStorage

### 4. Validace a Business Logika
**Potřebné úpravy:**

#### Photo Endpoint (`/api/photos`)
- ✅ Validace base64 formátu
- ✅ Kontrola velikosti (max 10MB)
- ⚠️ Potřebuje úpravu pro lepší error handling

#### Material Use Endpoint (`/api/materials/use`)
- ⚠️ Přidat kontrolu dostupnosti na skladě
- ⚠️ Vytvořit stock alert při nízkém stavu

#### Blocker Endpoint (`/api/blockers`)
- ⚠️ Přidat notifikace pro managery
- ⚠️ Aktualizovat risk score zakázky

### 5. Helper Funkce pro Dashboard Routes
**Potřebné:**
- `get_last_job_context(user)` - vrátí poslední zakázku uživatele
- `get_last_work_type(user)` - vrátí ID posledního typu práce
- `get_team_context(user)` - vrátí kontext týmu pro landera
- `get_widget_data(widget_id, user)` - načte data pro widget

## 📝 Implementační poznámky

### RBAC Systém
- Používá existující `require_auth()` funkci
- Kontroly oprávnění jsou inline v každém endpointu
- Vrací JSON error responses s HTTP status kódy

### Mode Switch
- Uživatelské preference jsou v `user_settings` tabulce
- Cookie backup pro rychlý přístup
- Auto mode podle role jako fallback

### Queue Stránka
- Zobrazuje pending items z localStorage
- Zobrazuje failed items s možností retry
- Zobrazuje recent synced items z DB

### Validace
- Base64 validace pro fotky
- Kontrola dostupnosti materiálu
- Notifikace pro managery při blockeru

## 🚀 Další kroky

1. Dokončit mode switch endpoint s cookie backup
2. Vytvořit queue stránku a template
3. Přidat validace do photo, material a blocker endpoints
4. Vytvořit helper funkce pro dashboard routes
5. Otestovat všechny funkce
