# green david app — minimální funkční základ s Brigádníky

## Lokální běh
```bash
python -m venv .venv && . .venv/bin/activate
pip install -r requirements.txt
gunicorn --workers 2 --threads 4 --timeout 120 --bind 0.0.0.0:8000 wsgi:app
# otevři http://localhost:8000/employees
```

## Render (Start Command)
```
gunicorn --workers 2 --threads 4 --timeout 120 --bind 0.0.0.0:$PORT wsgi:app
```

## Migrace DB
Doporučeno:
```
sqlite3 app.db < migrations/004_add_temps.sql
```
(První volání `/gd/api/temps` tabulku také umí vytvořit.)