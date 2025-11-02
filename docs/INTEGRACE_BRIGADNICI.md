# Integrace podsekce **Brigádníci** do sekce **Zaměstnanci**

Tento balíček přidává REST API a UI kartu *Brigádníci* (CRUD + CSV export). UI je česky, zelený styl zůstává.

## 1) Soubory nahraď/ přidej

Z kořene projektu vlož/nahraď následující cesty:

```
gd/api/__init__.py              # pokud nemáš, přidej (registruje /gd/api)
gd/api/employees.py             # NOVÉ/REWRITE: endpoints /gd/api/temps (brigádníci)
templates/employees.html        # úprava: přidána karta Brigádníci
static/js/employees.js          # front-end logika pro Brigádníky
migrations/004_add_temps.sql    # SQLite migrace
docs/INTEGRACE_BRIGADNICI.md    # tento návod
wsgi_patch_snippet.txt          # snippet k registraci blueprintu, pokud chybí
```

> **Pozn.:** Pokud už máš vlastní `gd/api/__init__.py` nebo `gd/api/employees.py`, porovnej diff a jen doplň části s `temps`.

## 2) Registrace blueprintu API (pokud ještě není)

Do `wsgi.py` (nebo místa, kde inicializuješ Flask aplikaci) přidej:

```python
from gd.api import register_api
register_api(app)  # zaregistruje blueprint /gd/api a endpoints
```

(Hotový snippet je v `wsgi_patch_snippet.txt`.)

## 3) Migrace DB (SQLite)

Spusť SQL z `migrations/004_add_temps.sql` proti souboru `app.db`:

```
sqlite3 app.db < migrations/004_add_temps.sql
```

Anebo nech první request na `/gd/api/temps` tabulku automaticky vytvořit (aplikace to umí), ale **doporučeno** je migraci spustit.

## 4) Odkaz v navigaci

Ujisti se, že stránka `/employees` (Zaměstnanci) odkazuje na šablonu `templates/employees.html`.
Karta **Brigádníci** je součástí této stránky a volá API `/gd/api/temps*`.

## 5) Test

Spusť jednoduché testy (pokud používáš pytest):

```
pytest -q
```

## 6) Endpoints přehled

- `GET /gd/api/temps` – seznam brigádníků
- `POST /gd/api/temps` – vytvořit
- `GET /gd/api/temps/<id>` – detail
- `PUT /gd/api/temps/<id>` – upravit
- `DELETE /gd/api/temps/<id>` – smazat
- `GET /gd/api/temps/export.csv` – CSV export

## 7) Poznámky k kompatibilitě

- Nezasahujeme do stávající logiky zaměstnanců; přidáváme samostatnou kartu.
- Pokud máš vlastní schéma/ORM, přemapuj dle potřeby v `gd/api/employees.py` (sekce `Brigádníci`).

---

*Green David – integrace Brigádníků. V případě potřeby upravím na míru tvému repu.*
