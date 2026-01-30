# Změny v main.py pro Crew Control System

## 1. Přidat na začátek souboru (po ostatních importech):

```python
# Crew Control System API
try:
    from crew_api import crew_bp
    CREW_API_AVAILABLE = True
except ImportError:
    CREW_API_AVAILABLE = False
    print("[INFO] Crew API module not available")
```

## 2. Přidat po vytvoření Flask app (app = Flask(...)):

```python
# Register Crew Control System API blueprint
if CREW_API_AVAILABLE:
    app.register_blueprint(crew_bp)
    print("[INFO] Crew Control System API registered")
```

## 3. V _ensure() funkci přidat volání migrace:

```python
# V try bloku po _migrate_roles_and_hierarchy():
_migrate_crew_control_tables()  # New: Crew Control System tables
```

## 4. Přidat novou funkci _migrate_crew_control_tables() (viz crew_migration v main.py)

Tato funkce vytváří všechny potřebné tabulky pro Crew Control System.

## 5. Aktualizovat route pro /team:

```python
@app.route("/team")
@app.route("/team/")
@app.route("/employees")
@app.route("/employees/")
def team_alias():
    # Prefer team.html (Crew Control System), fallback to employees.html
    try:
        return send_from_directory(".", "team.html")
    except:
        try:
            return render_template("employees.html")
        except:
            return send_from_directory(".", "employees.html")

@app.route("/team.html")
def team_html_direct():
    return send_from_directory(".", "team.html")
```

---

Kompletní aktualizovaný main.py je k dispozici v exportu.
