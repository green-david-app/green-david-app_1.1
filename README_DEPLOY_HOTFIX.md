
# green david app — Calendar hotfix (v1.2)

Tento balíček opravuje API kalendáře tak, aby:
- podporovalo i dotazy `?from=YYYY-MM-DD&to=YYYY-MM-DD` (kromě `?month=` a `?date=`),
- přidalo endpoint `PATCH /gd/api/calendar` pro úpravu záznamů,
- vracelo klíče `events` **i** `items` pro kompatibilitu více verzí frontendu.

## Co nahradit
V projektu nahraďte soubor:

- `app/api.py` (tímto souborem)

## Nasazení na Render
Start Command beze změny:
```
gunicorn --workers 2 --threads 4 --timeout 120 --bind 0.0.0.0:$PORT wsgi:app
```

## Rychlý test lokálně
```
python -m venv .venv && . .venv/bin/activate
pip install -r requirements.txt
export FLASK_APP=wsgi.py
flask run -p 5000
# Otevřete http://localhost:5000/calendar
# Přidání: tlačítka +Poznámka/+Úkol/+Zakázka → dialog → Uložit
```
