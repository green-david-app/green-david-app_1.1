
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
