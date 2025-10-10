# green david app — v1.1 (funkční build)

Interní webová aplikace pro správu zakázek, hodin, skladu a úkolů pro tým **green david**. Backend **Flask 3 + SQLite**, frontend je jednoduchý **React 18** přes CDN (UMD) vykreslovaný v `index.html`. Exporty do Excelu přes **openpyxl**. Nasazení přes **Gunicorn** (Docker/Procfile).

---

## 🚀 Rychlý start (lokálně)

**Požadavky:** Python 3.12+ (viz `runtime.txt`), `pip`

```bash
cd green-david-app_1.1_funkční
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt

# volitelné – nastav si bezpečné hodnoty (jinak se použijí defaulty)
export SECRET_KEY="$(python - <<'PY'
import os; print(os.urandom(24).hex())
PY)"
export ADMIN_EMAIL="admin@greendavid.local"
export ADMIN_PASSWORD="admin123"
export DB_PATH="app.db"
export UPLOAD_DIR="uploads"

python main.py  # běží na http://localhost:5000
```

První uživatel (seed) se vytvoří automaticky při prvním požadavku:
- **email:** `admin@greendavid.local` (lze změnit přes `ADMIN_EMAIL`)
- **heslo:** `admin123` (lze změnit přes `ADMIN_PASSWORD`)

> ⚠️ **Produkce:** nastav **vlastní `SECRET_KEY`** a **změň defaultní heslo**. SQLite soubor `app.db` ulož na perzistentní disk (volume).

---

## 🐳 Docker (produkční běh přes Gunicorn)

```bash
cd green-david-app_1.1_funkční

docker build -t green-david-app:1.1 .

# perzistence databáze a uploadů
mkdir -p ./data ./uploads

docker run --rm -it \
  -e SECRET_KEY=change_me \
  -e ADMIN_EMAIL=admin@greendavid.local \
  -e ADMIN_PASSWORD=super_secret \
  -e DB_PATH=/data/app.db \
  -e UPLOAD_DIR=/uploads \
  -v $(pwd)/data:/data \
  -v $(pwd)/uploads:/uploads \
  -p 8000:8000 \
  green-david-app:1.1
```

Aplikace bude dostupná na **http://localhost:8000**.

> Alternativně je k dispozici **Procfile** (`web: gunicorn -w 4 -b 0.0.0.0:8000 main:app`) a `runtime.txt` (Python 3.12.6) pro platformy typu Render/Fly/Heroku.

---

## 🧱 Datový model (SQLite tabulky)

```
- app_meta
- employees
- items
- job_assignments
- job_materials
- job_photos
- job_tools
- jobs
- tasks
- timesheets
- users
```

---

## 🔌 API map (výňatek)

| Metody | Cesta | Funkce |
|---|---|---|
| GET | `/` | `index` |
| GET | `/uploads/<path:name>` | `uploaded_file` |
| GET | `/health` | `health` |
| GET | `/api/me` | `api_me` |
| POST | `/api/login` | `api_login` |
| POST | `/api/logout` | `api_logout` |
| GET, POST, PATCH | `/api/users` | `api_users` |
| GET, POST, DELETE | `/api/employees` | `api_employees` |
| GET, POST, DELETE | `/api/timesheets` | `api_timesheets` |
| GET, POST, PATCH, DELETE | `/api/items` | `api_items` |
| GET, POST | `/api/jobs` | `api_jobs` |
| GET | `/api/jobs/<int:jid>` | `api_job_detail` |
| POST, DELETE | `/api/jobs/<int:jid>/materials` | `api_job_materials` |
| POST, DELETE | `/api/jobs/<int:jid>/tools` | `api_job_tools` |
| POST, DELETE | `/api/jobs/<int:jid>/photos` | `api_job_photos` |
| GET, POST | `/api/jobs/<int:jid>/assignments` | `api_job_assignments` |
| GET, POST, PATCH, DELETE | `/api/tasks` | `api_tasks` |
| GET | `/export/employee_hours.xlsx` | `export_employee_hours` |
| GET | `/export/job_materials.xlsx` | `export_job_materials` |
| GET | `/export/warehouse.xlsx` | `export_warehouse` |

> Autentizace přes sessions (Flask). Role: `admin`, `manager`, `worker`. Základní pravidlo: zápisové operace vyžadují `admin/manager`, čtení vyžaduje přihlášení (viz `require_auth()` / `require_role()` v `main.py`).

### Příklady (curl)

**Login → session cookie:**
```bash
curl -i -c cookies.txt -H "Content-Type: application/json" \
  -d '{"email":"admin@greendavid.local","password":"admin123"}' \
  http://localhost:5000/api/login
```

**Seznam zakázek:**
```bash
curl -b cookies.txt http://localhost:5000/api/jobs
```

**Nová zakázka:**
```bash
curl -b cookies.txt -H "Content-Type: application/json" -X POST \
  -d '{"title":"Záhon u školy","client":"ZŠ Lipník","status":"Plán","city":"Lipník","code":"2025-091","date":"2025-10-11","note":""}' \
  http://localhost:5000/api/jobs
```

**Export hodin zaměstnance (XLSX):**
```bash
curl -b cookies.txt -L -o employee_hours.xlsx "http://localhost:5000/export/employee_hours.xlsx?employee_id=1&from=2025-01-01&to=2025-12-31"
```

---

## 🖼️ Uploady

- Ukládají se do složky `uploads` (lze změnit proměnnou `UPLOAD_DIR`).
- Názvy souborů jsou sanitizované, přístup přes `/uploads/<filename>`.
- Doporučeno mít uploady na perzistentním svazku (Docker volume).

---

## 🔐 Bezpečnost & nasazení

- **SECRET_KEY** nastavuj unikátní, dlouhý (např. 32+ bajtů hex).
- **Admin heslo** změň hned po prvním spuštění (pomocí `ADMIN_PASSWORD` nebo přes UI).
- Pro veřejné nasazení dej před aplikaci reverzní proxy (TLS, rate limit), případně osnovu VPN / interní sítě.
- SQLite je super pro single-node; při škálování zvaž PostgreSQL + SQLAlchemy (migrace).

---

## 🛣️ Roadmap návrh v1.2

- Filtry & fulltext u seznamů (zakázky, sklady, úkoly).
- Notifikace k úkolům (termíny) – e-mail / webhook.
- Validace a masky dat (datum, počet hodin) i na klientu.
- Import CSV pro sklady a hodiny.
- Přístupová práva per oddělení (Lipník/Praha), audit-logy.
- Obrázky – limity velikosti, jednoduchý resizer/thumbnailer.

---

*Generováno: {today}*
