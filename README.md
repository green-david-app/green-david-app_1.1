
# green david app (Kalendář + Výkazy)

Hotová základní verze s českým UI (zelené téma). Obsahuje:
- Stránky **/calendar** a **/timesheets**
- API pod **/gd/api/** (employees, jobs, tasks, calendar, timesheets)
- SQLite **app.db** (vytvoří se automaticky při startu)
- Export výkazů do CSV na **/timesheets/export.csv**
- WSGI entrypoint `wsgi:app`

## Lokální spuštění
```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
gunicorn --workers 2 --threads 4 --timeout 120 --bind 0.0.0.0:5000 wsgi:app
# otevři http://localhost:5000/calendar
```

## Nasazení na Render
Start Command:
```
gunicorn --workers 2 --threads 4 --timeout 120 --bind 0.0.0.0:$PORT wsgi:app
```


## Hotfix 1.2.1 (Render deploy fix)
- Přidán `runtime.txt` s **python-3.11.9**, aby se na Renderu nepoužil Python 3.13.
- `SQLAlchemy==2.0.32` (kompatibilní vydání 2.0.x).
- Přidán `Procfile` pro jistotu.

Pokud jste nasazovali na Pythonu 3.13 a viděli AssertionError v SQLAlchemy, tento balíček to řeší.
