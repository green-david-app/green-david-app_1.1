# AUDIT: Mobile FIELD/FULL Systém

## ✅ NALEZENO

### 1. MODE SWITCH (FIELD/FULL)
- [x] **`get_mobile_mode()` funkce**: `app/utils/mobile_mode.py`, řádek 83
- [x] **`user_settings` tabulka**: `main.py`, řádek 1321 (migrace v29)
- [x] **`PATCH /api/user/settings` endpoint**: `main.py`, řádek 3222
- [x] **Mode toggle v headeru**: 
  - `templates/layouts/layout_mobile_field.html`, řádek 32
  - `templates/layouts/layout_mobile_full.html`, řádek 25
  - `static/js/mode.js` - kompletní implementace toggle funkce

### 2. WIDGET SYSTÉM
- [x] **`WIDGET_REGISTRY` slovník**: `config/widgets.py`, řádek 7
- [x] **`ROLE_DEFAULT_WIDGETS` konfigurace**: `config/widgets.py`, řádek 144
- [x] **Složka `templates/widgets/`**: Existuje s 13 widget templates:
  - `add_photo.html`, `budget_burn.html`, `current_job.html`, `jobs_risk.html`
  - `material_quick.html`, `my_tasks.html`, `notifications.html`, `offline_status.html`
  - `overdue_jobs.html`, `quick_log.html`, `report_blocker.html`, `stock_alerts.html`, `team_load.html`
- [x] **`get_user_widgets()` funkce**: `app/utils/widgets.py`, řádek 30

### 3. RBAC SYSTÉM
- [x] **User model má pole `role`**: `main.py`, řádek 1291 (migrace v28)
- [x] **`ROLE_PERMISSIONS` slovník**: `config/permissions.py`, řádek 31
- [x] **`has_permission()` funkce**: `app/utils/permissions.py`, řádek 48
- [x] **`@require_permission` dekorátor**: `app/utils/permissions.py`, řádek 56
- [x] **RBAC kontroly na endpoints**: 
  - Widget endpoints mají RBAC kontroly (main.py řádky 14373-14583)
  - Quick action endpoints mají RBAC kontroly (main.py řádky 14589-14906)

### 4. ROUTES
- [x] **`/mobile/today` route**: `main.py`, řádek 13952
- [x] **`/mobile/dashboard` route**: `main.py`, řádek 13830
- [x] **`/mobile/queue` route**: `main.py`, řádek 14273
- [x] **Další mobile routes**:
  - `/mobile/tasks`: `main.py`, řádek 14147
  - `/mobile/photos`: `main.py`, řádek 14190
  - `/mobile/notifications`: `main.py`, řádek 14233
  - `/mobile/edit-dashboard`: `main.py`, řádek 14032

## ⚠️ ČÁSTEČNĚ (rozpracované)

### 1. Mode Switch
- [x] Funkce existuje a funguje
- [x] Endpoint existuje a funguje
- [x] Cookie backup je implementován
- [ ] **CHYBÍ**: Context processor pro `get_mobile_mode()` v templates (částečně řešeno přes `inject_permissions()`)

### 2. Widget Systém
- [x] Registry existuje
- [x] Templates existují
- [x] Helper funkce existují
- [ ] **CHYBÍ**: Helper funkce pro načítání dat widgetů (`get_last_job_context`, `get_last_work_type`, atd.) - jsou použity inline v routes

### 3. RBAC Systém
- [x] Permissions map existuje
- [x] Dekorátory existují
- [x] Kontroly na endpoints jsou implementovány
- [ ] **CHYBÍ**: `@require_permission` dekorátor není používán jako dekorátor, ale jako inline kontrola (funguje, ale není konzistentní)

## ❌ CHYBÍ (nutno implementovat)

### 1. Validace a Business Logika
- [ ] **Photo endpoint**: Rozšířená validace base64 (částečně implementováno, ale může být lepší)
- [ ] **Material Use endpoint**: Kontrola dostupnosti na skladě před odepsáním (částečně implementováno)
- [ ] **Blocker endpoint**: Notifikace pro managery při vytvoření blockeru (částečně implementováno)
- [ ] **Risk Score**: Automatická aktualizace risk score zakázky při vytvoření blockeru

### 2. Helper Funkce pro Dashboard
- [ ] `get_last_job_context(user)` - vrátí poslední zakázku uživatele
- [ ] `get_last_work_type(user)` - vrátí ID posledního typu práce
- [ ] `get_team_context(user)` - vrátí kontext týmu pro landera
- [ ] `get_widget_data(widget_id, user)` - načte data pro widget

### 3. Offline Queue
- [x] Route existuje
- [x] Template existuje
- [x] JavaScript pro zobrazení queue existuje
- [ ] **CHYBÍ**: Rozšířené funkce v `OfflineQueue` objektu (`forceSync`, `clearFailed`) - jsou definovány v template, ale měly by být v `static/js/offline-queue.js`

## 🐛 BONUS: OPRAVA CHYBY - "undefined má nízké zásoby"

### Problém nalezen:
V `main.py` řádek 12392 je správně použito `item['name']`, ale problém může být v API endpointu `/api/widgets/stock-alerts` (řádek 14428).

### Kontrola:
```python
# main.py řádek 14428-14528
@app.route('/api/widgets/stock-alerts')
def api_widget_stock_alerts():
    # ...
    alerts = db.execute("""
        SELECT name as material_name, 
               quantity,
               unit,
               CASE 
                   WHEN quantity <= 0 THEN 'critical'
                   WHEN quantity < min_stock THEN 'warning'
                   ELSE 'info'
               END as severity,
               'Nízká zásoba' as message
        FROM warehouse_items
        WHERE (quantity <= 0 OR quantity < COALESCE(min_stock, 5))
          AND (status = 'active' OR status IS NULL)
        ORDER BY 
            CASE WHEN quantity <= 0 THEN 0 ELSE 1 END,
            quantity ASC
        LIMIT 10
    """).fetchall()
```

**Problém**: Pokud `name` je NULL v databázi, bude zobrazeno jako `None` nebo prázdný string.

**Řešení**: Přidat `COALESCE(name, 'Neznámá položka')` do SQL dotazu.

**✅ OPRAVENO**: `main.py` řádek 14545 - přidán `COALESCE(name, 'Neznámá položka')` do SQL dotazu v `/api/widgets/stock-alerts` endpointu.
