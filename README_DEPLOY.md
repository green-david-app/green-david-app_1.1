
# green david app — Calendar fix 1.2

Tato verze opravuje stránku **/calendar**: umožňuje přidávat záznamy (Poznámka, Úkol, Zakázka), přiřadit barvu, a záznamy mazat. Data se ukládají do SQLite `app.db` (tabulka `events`).

## Lokální spuštění

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
export FLASK_APP=wsgi.py
flask run -p 5000
# otevřete http://localhost:5000/calendar
```

## Render.com

Start Command:

```
gunicorn --workers 2 --threads 4 --timeout 120 --bind 0.0.0.0:$PORT wsgi:app
```

## API

- `GET /gd/api/calendar?month=YYYY-MM` – vrátí záznamy daného měsíce
- `POST /gd/api/calendar` – vytvoří záznam (JSON: date, title, type[note|task|job], color, details)
- `DELETE /gd/api/calendar/<id>` – smaže záznam

## Poznámky

- Při prvním spuštění se databáze sama vytvoří.
- Dvojklikem do buňky dne také otevřete přidání záznamu.
