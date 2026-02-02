# Souhrn změn - Routes a API Endpoints

## Přidané Routes

### Mobile UI Routes

1. **`/mobile/tasks`** - Stránka s úkoly
   - Zobrazuje úkoly přihlášeného uživatele
   - Podporuje změnu statusu úkolu
   - Template: `templates/mobile/tasks.html`

2. **`/mobile/photos`** - Stránka s fotografiemi
   - Zobrazuje fotografie uživatele nebo konkrétní zakázky
   - Podporuje modal pro zobrazení fotografie
   - Template: `templates/mobile/photos.html`

3. **`/mobile/notifications`** - Stránka s notifikacemi
   - Zobrazuje notifikace uživatele
   - Automaticky označuje jako přečtené při načtení
   - Template: `templates/mobile/notifications.html`

## Přidané API Endpoints

### Widget Data Endpoints

1. **`GET /api/widgets/jobs-risk`**
   - Vrací rizikové zakázky s blokery nebo zpožděním
   - Response: `{ok: true, risky_jobs: [...]}`

2. **`GET /api/widgets/overdue-jobs`**
   - Vrací zpožděné zakázky
   - Response: `{ok: true, overdue_jobs: [...]}`

3. **`GET /api/widgets/team-load`**
   - Vrací vytížení týmu (hodiny za den)
   - Response: `{ok: true, team_members: [...]}`

4. **`GET /api/widgets/stock-alerts`**
   - Vrací skladové výstrahy (nízké zásoby)
   - Response: `{ok: true, alerts: [...]}`

5. **`GET /api/widgets/budget-burn`**
   - Vrací data o čerpání rozpočtu
   - Response: `{ok: true, budget_data: {...}}`

### Quick Actions Endpoints

1. **`POST /api/worklogs`**
   - Vytvoří worklog z mobilu
   - Podporuje deduplikaci přes `X-Event-ID` header
   - Body: `{job_id, duration, work_type_id?, note?, created_at?}`
   - Response: `{ok: true, id, status: 'created'}`

2. **`POST /api/photos`**
   - Nahrání fotografie z mobilu
   - Podporuje deduplikaci přes `X-Event-ID` header
   - Body: `{job_id, image_data (base64), tag?, created_at?}`
   - Response: `{ok: true, id, photo_url, status: 'created'}`

3. **`POST /api/materials/use`**
   - Odepsání materiálu z mobilu
   - Podporuje deduplikaci přes `X-Event-ID` header
   - Body: `{material_id, quantity, job_id}`
   - Response: `{ok: true, material_id, quantity_used, remaining, status: 'deducted'}`

4. **`POST /api/blockers`**
   - Vytvoření blockeru/problému z mobilu
   - Podporuje deduplikaci přes `X-Event-ID` header
   - Body: `{job_id, type?, description, photo_data? (base64)}`
   - Response: `{ok: true, id, status: 'created', message}`

5. **`GET /api/materials/search`**
   - Vyhledávání materiálu
   - Query: `?q=<query>`
   - Response: `{ok: true, items: [...]}`

### Offline Queue Endpoints

1. **`POST /api/offline/queue`**
   - Synchronizace offline queue - zpracování více eventů najednou
   - Body: `{events: [{id, type, data}]}`
   - Podporované typy: `worklog_create`, `photo_add`, `material_use`, `blocker_create`
   - Response: `{ok: true, processed: [...], failed: [...], total, success_count, failed_count}`

2. **`GET /api/offline/status`**
   - Kontrola offline statusu serveru
   - Response: `{ok: true, online: true/false, server_time, message}`

## Database Migrations

### Migration v31: ProcessedEvents Table

Vytvořena tabulka `processed_events` pro deduplikaci offline queue:

```sql
CREATE TABLE IF NOT EXISTS processed_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    event_id TEXT UNIQUE NOT NULL,
    event_type TEXT NOT NULL,
    result_id INTEGER,
    created_at TEXT DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_processed_events_event_id ON processed_events(event_id);
CREATE INDEX IF NOT EXISTS idx_processed_events_type ON processed_events(event_type);
```

## Deduplikace

Všechny quick action endpoints podporují deduplikaci pomocí `X-Event-ID` headeru:

- Pokud je `X-Event-ID` poslán, endpoint zkontroluje, zda event již nebyl zpracován
- Pokud ano, vrátí `409 Conflict` s informací o duplicitě
- Pokud ne, zpracuje event a zaznamená ho do `processed_events` tabulky

## Offline Queue Flow

1. **Uživatel je offline:**
   - Akce se ukládají do lokální queue (IndexedDB/localStorage)
   - Každá akce má unikátní `event_id` (UUID)

2. **Uživatel je online:**
   - Frontend volá `/api/offline/queue` s batch eventů
   - Backend zpracuje každý event:
     - Zkontroluje deduplikaci
     - Vytvoří záznam
     - Zaznamená do `processed_events`
   - Vrátí seznam úspěšných a neúspěšných eventů

3. **Frontend:**
   - Odstraní úspěšné eventy z queue
   - Zobrazí chyby pro neúspěšné eventy

## Změněné soubory

1. **`main.py`**
   - Přidány nové routes pro mobile UI
   - Přidány nové API endpoints
   - Přidána migrace v31
   - Rozšířena logika pro offline queue

2. **`templates/mobile/tasks.html`** (nový)
   - Template pro zobrazení úkolů

3. **`templates/mobile/photos.html`** (nový)
   - Template pro zobrazení fotografií

4. **`templates/mobile/notifications.html`** (nový)
   - Template pro zobrazení notifikací

## Testování

### Test API Endpoints

1. **Widget Data:**
   ```bash
   curl http://localhost:5000/api/widgets/jobs-risk
   curl http://localhost:5000/api/widgets/overdue-jobs
   curl http://localhost:5000/api/widgets/team-load
   curl http://localhost:5000/api/widgets/stock-alerts
   curl http://localhost:5000/api/widgets/budget-burn
   ```

2. **Quick Actions:**
   ```bash
   # Worklog
   curl -X POST http://localhost:5000/api/worklogs \
     -H "Content-Type: application/json" \
     -H "X-Event-ID: test-123" \
     -d '{"job_id": 1, "duration": 60, "note": "Test"}'
   
   # Photo
   curl -X POST http://localhost:5000/api/photos \
     -H "Content-Type: application/json" \
     -H "X-Event-ID: test-124" \
     -d '{"job_id": 1, "image_data": "base64data..."}'
   
   # Material Use
   curl -X POST http://localhost:5000/api/materials/use \
     -H "Content-Type: application/json" \
     -H "X-Event-ID: test-125" \
     -d '{"material_id": 1, "quantity": 5, "job_id": 1}'
   
   # Blocker
   curl -X POST http://localhost:5000/api/blockers \
     -H "Content-Type: application/json" \
     -H "X-Event-ID: test-126" \
     -d '{"job_id": 1, "description": "Test blocker"}'
   ```

3. **Offline Queue:**
   ```bash
   curl -X POST http://localhost:5000/api/offline/queue \
     -H "Content-Type: application/json" \
     -d '{
       "events": [
         {"id": "event-1", "type": "worklog_create", "data": {"job_id": 1, "duration": 60}},
         {"id": "event-2", "type": "photo_add", "data": {"job_id": 1, "image_data": "..."}}
       ]
     }'
   ```

### Test Routes

1. Otevřít v prohlížeči:
   - `http://localhost:5000/mobile/tasks`
   - `http://localhost:5000/mobile/photos`
   - `http://localhost:5000/mobile/notifications`

2. Ověřit, že se stránky načítají správně
3. Ověřit, že data se zobrazují správně
4. Ověřit, že akce fungují (změna statusu úkolu, atd.)

## Poznámky

- Všechny endpoints vyžadují autentizaci (kromě demo routes)
- Offline queue podporuje batch zpracování pro efektivitu
- Deduplikace zajišťuje, že stejný event není zpracován dvakrát
- Všechny quick actions podporují offline mode s queue
