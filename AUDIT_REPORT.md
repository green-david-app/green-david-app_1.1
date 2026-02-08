# Green David App — Audit Report

**Datum:** 2026-02-03

> **Poznámka:** Tento audit analyzuje strukturu a kvalitu kódu bez oprav. Zaměřuje se na problémy které by měly být řešeny.

---

## Shrnutí

- **Celkem souborů:** 162
- **Celkem řádků kódu:** 109,284
- **Python souborů:** 31 (28,275 řádků)
- **HTML souborů:** 63 (47,278 řádků)
- **CSS souborů:** 19 (15,797 řádků)
- **JS souborů:** 49 (17,934 řádků)

**Statistiky:**
- **Kritických problémů:** 3
- **Varování:** 3
- **Doporučení:** 5+

---

## 🔴 Kritické problémy (musí se opravit)

### 1. main.py je PŘÍLIŠ VELKÝ

**Problém:** `main.py` má **12,951 řádků**, **286 funkcí**, **224 route handlerů**.

**Proč je to problém:**
- Nemožné navigovat v kódu
- Konflikty při merge
- Špatná udržovatelnost
- Porušuje Single Responsibility Principle
- IDE zpomaluje při otevírání souboru

**Doporučené řešení:**
Rozdělit na moduly:

```
app/
  __init__.py          # Flask app inicializace
  routes/
    __init__.py
    jobs.py            # Všechny /jobs routes
    tasks.py           # Všechny /tasks routes
    mobile.py          # Všechny /mobile routes
    api.py             # Všechny /api routes
    auth.py            # Login, logout, register
    employees.py       # /team, /employees routes
    warehouse.py       # /warehouse routes
    planning.py        # /planning-* routes
  models/
    __init__.py
    user.py            # User model + helper funkce
    job.py             # Job model + helper funkce
    employee.py        # Employee model
  utils/
    __init__.py
    db.py              # DB connection, migrace
    permissions.py     # RBAC funkce
  config.py           # Konfigurace
main.py                # Entry point (pouze app.run())
```

**Postup:**
1. Vytvořit strukturu složek
2. Přesunout routes do `routes/` podle funkcionality
3. Přesunout modely do `models/`
4. Přesunout utility do `utils/`
5. V `main.py` pouze importovat a spustit app

---

### 2. Bare except bloky

**Problém:** Nalezeno **9 `except Exception:`** bloků bez specifikace konkrétní výjimky.

**Proč je to problém:**
- Skrývá všechny chyby včetně systémových
- Ztěžuje debugging
- Může způsobit neočekávané chování

**Příklady v kódu:**
- Řádek 56: `except Exception: pass`
- Řádek 105: `except Exception as e:`
- Řádek 120: `except Exception: pass`
- Řádek 128: `except Exception: return False`
- Řádek 140: `except Exception: return False`

**Doporučené řešení:**
Vždy specifikovat konkrétní výjimku:
```python
# ŠPATNĚ:
try:
    # kód
except Exception:  # ❌
    pass

# SPRÁVNĚ:
try:
    # kód
except sqlite3.Error as e:  # ✅
    logger.error(f'DB chyba: {e}')
except ValueError as e:
    logger.error(f'Neplatná hodnota: {e}')
```

---

### 3. SQL Injection riziko

**Problém:** Nalezeno **potenciálně nebezpečné SQL dotazy** které používají f-string formatting místo parametrizace.

**Proč je to problém:**
- Uživatelský input může být přímo vložen do SQL
- Možnost SQL injection útoku
- Kritické bezpečnostní riziko

**Příklady v kódu:**
- Řádek 126: `db.execute(f"PRAGMA table_info({table})")` — `table` může být z uživatelského inputu
- Řádek 836: `db.execute(f"ALTER TABLE employees ADD COLUMN {col_name} {col_def}")` — dynamické DDL
- Řádek 1600: Podobné DDL dotazy

**Poznámka:** Některé dotazy používají f-string pro DDL (CREATE TABLE, ALTER TABLE), což je méně rizikové než DML, ale stále by mělo být validováno.

**Doporučené řešení:**
Vždy používat parametrizované dotazy pro DML:
```python
# ŠPATNĚ:
cursor.execute(f'SELECT * FROM users WHERE id = {user_id}')  # ❌

# SPRÁVNĚ:
cursor.execute('SELECT * FROM users WHERE id = ?', (user_id,))  # ✅
```

Pro DDL použít whitelist validaci:
```python
ALLOWED_TABLES = ['users', 'jobs', 'tasks']
if table not in ALLOWED_TABLES:
    raise ValueError(f'Neplatná tabulka: {table}')
```

---

## ⚠️ Varování (mělo by se opravit)

### 1. Dlouhé funkce

Nalezeno **66+ funkcí delších než 50 řádků**.

**Doporučení:** Funkce by měly být kratší a dělat jednu věc (Single Responsibility Principle).

**Nejdelší funkce:**
- `apply_migrations()`: řádky 154-551 (**398 řádků**)
- `ensure_schema()`: řádky 1051-1313 (**263 řádků**)
- `_migrate_crew_control_tables()`: řádky 1462-1608 (**147 řádků**)
- `generate_auto_notifications()`: řádky 1776-1942 (**167 řádků**)
- `api_employees()`: řádky 2088-2314 (**227 řádků**)

**Doporučení:** Rozdělit dlouhé funkce na menší, logicky oddělené části.

---

### 2. Nadměrné použití `!important` v CSS

Nalezeno **1,131 výskytů `!important`** v CSS souborech.

**Proč je to problém:**
- Značí problémy s CSS specificitou
- Ztěžuje přepisování stylů
- Může způsobit neočekávané chování
- Ztěžuje údržbu

**Nejhorší soubory:**
- `static/style.css`: **376** `!important`
- `static/css/app.css`: **162** `!important`
- `static/css/job-detail.css`: **101** `!important`
- `static/css/sidebar.css`: **35** `!important`

**Doporučení:**
- Používat specifičtější selektory místo `!important`
- Zkontrolovat CSS architekturu
- Zvážit CSS metodologii (BEM, CSS Modules)

---

### 3. Console.log v produkci

Nalezeno **142 výskytů `console.log`** v JS souborech.

**Doporučení:**
- Odstranit nebo nahradit loggerem
- Použít podmíněné logování pro development:
```javascript
const DEBUG = window.location.hostname === 'localhost';
const log = DEBUG ? console.log : () => {};
```

**Nejhorší soubory:**
- `static/js/gps-tracker.js`: **13** console.log
- `static/js/task-detail-modal.js`: **13** console.log
- `static/js/smart-notifications.js`: **14** console.log
- `static/js/ai-operator-drawer.js`: **11** console.log

---

## 📋 Detailní analýza po souborech

### main.py

- **Řádků:** 12,951
- **Funkcí:** 286
- **Route handlerů:** 224
- **TODO/FIXME:** 0 (nenalezeno)
- **Import statements:** 96

**Problémy:**
- ⚠️ Příliš velký (12,951 řádků) — rozdělit na moduly
- ⚠️ 66+ dlouhých funkcí (>50 řádků)
- ⚠️ 9 `except Exception:` bloků

**Doporučení:**
1. Rozdělit na moduly podle funkcionality
2. Přesunout migrace do samostatného modulu
3. Přesunout API endpoints do `routes/api.py`
4. Přesunout helper funkce do `utils/`

---

### HTML soubory

**Statistiky:**
- **Celkem:** 63 souborů (47,278 řádků)
- **S sidebarem:** 34 souborů
- **Bez sidebaru:** 29 souborů (většinou v `app/templates/`)
- **S inline style:** 35 souborů
- **S inline script:** 48 souborů
- **Jinja šablony:** 29 souborů

**Největší HTML soubory:**
- `jobs.html`: **4,091 řádků**
- `index.html`: **2,541 řádků**
- `jobs-new.html`: **2,255 řádků**
- `nursery.html`: **2,175 řádků**
- `job-detail.html`: **2,119 řádků**

**Problémy:**
- ⚠️ Některé HTML soubory jsou velmi velké (4000+ řádků)
- ⚠️ Mnoho inline stylů a skriptů — měly by být v externích souborech
- ⚠️ 29 HTML souborů bez sidebaru (většinou v `app/templates/`)

**Doporučení:**
1. Extrahovat inline styly do CSS souborů
2. Extrahovat inline skripty do JS souborů
3. Zvážit rozdělení velkých HTML souborů na komponenty
4. Přidat sidebar do všech desktop stránek

---

### CSS soubory

**Statistiky:**
- **Celkem:** 19 souborů (15,797 řádků)
- **Celkem `!important`:** 1,131
- **Duplicitní selektory:** 71+ mezi soubory

**Největší CSS soubory:**
- `static/css/app.css`: **7,053 řádků**, 162 `!important`
- `static/style.css`: **2,097 řádků**, 376 `!important`
- `static/css/jobs.css`: **1,329 řádků**, 47 `!important`
- `static/css/job-detail.css`: **888 řádků**, 101 `!important`
- `static/css/layout.css`: **570 řádků**, 0 `!important` ✅

**Problémy:**
- ⚠️ Nadměrné použití `!important` (1,131x)
- ⚠️ Duplicitní selektory mezi soubory (konflikty)
- ⚠️ `static/style.css` a `style.css` jsou duplicitní (stejný obsah)

**Doporučení:**
1. Odstranit duplicitní `style.css` v kořeni
2. Refaktorovat CSS architekturu
3. Používat specifičtější selektory místo `!important`
4. Zvážit CSS metodologii (BEM)

---

### JavaScript soubory

**Statistiky:**
- **Celkem:** 49 souborů (17,934 řádků)
- **Celkem `console.log`:** 142
- **Hardcoded URL:** 500+ výskytů

**Největší JS soubory:**
- `static/js/ai-jobs-integration.js`: **1,510 řádků**, 4 console.log
- `static/js/ai-operator-drawer.js`: **1,223 řádků**, 11 console.log
- `static/warehouse/items.js`: **1,201 řádků**, 8 console.log
- `static/js/smart-notifications.js`: **725 řádků**, 14 console.log
- `static/js/gps-tracker.js`: **684 řádků**, 13 console.log

**Problémy:**
- ⚠️ Console.log v produkci (142x)
- ⚠️ Hardcoded URL místo relativních cest nebo konfigurace
- ⚠️ Některé soubory jsou velmi velké (1500+ řádků)

**Doporučení:**
1. Odstranit nebo podmíněně logovat console.log
2. Používat relativní cesty nebo konfiguraci pro URL
3. Rozdělit velké JS soubory na moduly

---

## 🔒 Bezpečnostní analýza

### Autentizace

- **`@login_required`:** 0x (nepoužívá se)
- **`require_auth`:** 67x (vlastní dekorátor)

**Status:** ✅ Autentizace je implementována pomocí vlastního `require_auth` dekorátoru.

---

### Hesla

- **Hashování:** ✅ Používá se `generate_password_hash` a `check_password_hash` z `werkzeug.security`
- **Algoritmus:** `pbkdf2:sha256` (bezpečný)

**Status:** ✅ Hesla jsou správně hashována.

---

### Session

- **Secure cookies:** ❌ NENÍ nastaveno
- **HttpOnly cookies:** ❌ NENÍ nastaveno
- **SameSite:** ❌ NENÍ nastaveno

**Problém:** Session cookies nejsou chráněné proti XSS a CSRF útokům.

**Doporučení:**
```python
app.config['SESSION_COOKIE_SECURE'] = True  # HTTPS only
app.config['SESSION_COOKIE_HTTPONLY'] = True  # No JS access
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'  # CSRF protection
```

---

### CSRF ochrana

- **Status:** ❌ CSRF ochrana NENÍ implementována

**Problém:** Aplikace je zranitelná vůči CSRF útokům.

**Doporučení:**
Implementovat Flask-WTF nebo Flask-SeaSurf:
```python
from flask_wtf.csrf import CSRFProtect
csrf = CSRFProtect(app)
```

---

### SQL Injection

- **Status:** ⚠️ Částečně chráněno
- **Parametrizované dotazy:** Většina DML dotazů používá parametrizaci
- **Riziko:** Některé DDL dotazy používají f-string formatting

**Doporučení:**
- Všechny dotazy s uživatelským inputem musí být parametrizované
- DDL dotazy musí validovat input proti whitelistu

---

## 📐 Konzistence kódu

### Pojmenování souborů

**Python:**
- ✅ Většinou `snake_case` (konzistentní)
- ✅ Výjimky: `ai_operator_*.py` (konzistentní prefix)

**HTML:**
- ✅ Většinou `kebab-case` (konzistentní)
- ✅ Výjimky: `employee-detail.html`, `job-detail.html` (konzistentní)

**CSS:**
- ✅ Většinou `kebab-case` (konzistentní)
- ✅ Výjimky: `app.css`, `style.css` (konzistentní)

**JavaScript:**
- ✅ Mix `kebab-case` a `camelCase` (částečně konzistentní)

**Status:** ✅ Celkově konzistentní pojmenování.

---

### CSS třídy

**Analýza `sidebar.css`:**
- **Kebab-case:** 122 tříd ✅
- **CamelCase:** 0 tříd
- **Snake_case:** 0 tříd

**Status:** ✅ Konzistentní kebab-case pojmenování.

---

### Odsazení

- **Používá se:** Mezery (4 mezery)
- **Konzistence:** ✅ Konzistentní napříč soubory

---

### Komentáře

- **Jazyk:** Mix češtiny a angličtiny
- **Kvalita:** Většinou popisné komentáře

**Doporučení:** Zvolit jeden jazyk pro komentáře (doporučeno angličtina pro mezinárodní tým).

---

## 🗑️ Mrtvý kód (doporučeno smazat)

### Zakomentovaný kód

- **V main.py:** ~849 řádků zakomentovaného kódu
- **Doporučení:** Odstranit nebo přesunout do `ARCHIVE.md` pokud je historicky důležitý

---

### Duplicitní soubory

- **`style.css` vs `static/style.css`:** Stejný obsah (2,097 řádků)
- **Doporučení:** Odstranit jeden z nich

---

## 🔄 Duplicity (sloučit)

### HTML soubory se stejným názvem

Nenalezeny duplicity se stejným názvem v různých složkách.

---

### CSS konflikty

- **Duplicitní selektory:** 71+ mezi různými CSS soubory
- **Problém:** Stejný selektor má různé hodnoty v různých souborech

**Doporučení:**
1. Zkontrolovat pořadí načítání CSS souborů
2. Sloučit konfliktní pravidla
3. Používat specifičtější selektory

---

## 💡 Doporučení pro refaktoring

### 1. Rozdělení main.py na moduly

**Priorita:** 🔴 VYSOKÁ

**Postup:**
1. Vytvořit strukturu `app/` složky
2. Přesunout routes do `routes/` podle funkcionality
3. Přesunout modely do `models/`
4. Přesunout utility do `utils/`
5. V `main.py` pouze importovat a spustit app

**Odhadovaný čas:** 2-3 dny

---

### 2. CSS refaktoring

**Priorita:** 🟡 STŘEDNÍ

**Postup:**
1. Odstranit duplicitní `style.css`
2. Refaktorovat CSS architekturu
3. Snížit použití `!important` na minimum
4. Zvážit CSS metodologii (BEM)

**Odhadovaný čas:** 1-2 dny

---

### 3. JavaScript cleanup

**Priorita:** 🟡 STŘEDNÍ

**Postup:**
1. Odstranit nebo podmíněně logovat console.log
2. Nahradit hardcoded URL konfigurací
3. Rozdělit velké JS soubory na moduly

**Odhadovaný čas:** 1 den

---

### 4. Bezpečnostní vylepšení

**Priorita:** 🔴 VYSOKÁ

**Postup:**
1. Nastavit secure session cookies
2. Implementovat CSRF ochranu
3. Validovat všechny SQL dotazy

**Odhadovaný čas:** 1 den

---

### 5. HTML refaktoring

**Priorita:** 🟢 NÍZKÁ

**Postup:**
1. Extrahovat inline styly do CSS
2. Extrahovat inline skripty do JS
3. Přidat sidebar do všech desktop stránek

**Odhadovaný čas:** 1-2 dny

---

## 📊 Shrnutí priorit

### Kritické (opravit ihned)
1. ✅ Rozdělení main.py na moduly
2. ✅ Bezpečnostní vylepšení (CSRF, secure cookies)
3. ✅ SQL injection prevence

### Důležité (opravit brzy)
1. ⚠️ CSS refaktoring (snížit !important)
2. ⚠️ JavaScript cleanup (console.log)
3. ⚠️ Dlouhé funkce (refaktoring)

### Vylepšení (opravit později)
1. 💡 HTML refaktoring (inline styly/skripty)
2. 💡 Odstranění mrtvého kódu
3. 💡 Konzistence komentářů

---

## ✅ Závěr

Aplikace Green David App je **funkční**, ale potřebuje **refaktoring** pro lepší udržovatelnost a bezpečnost.

**Hlavní problémy:**
1. **main.py je příliš velký** (12,951 řádků) — kritické pro udržovatelnost
2. **Bezpečnostní rizika** (CSRF, session cookies) — kritické pro produkci
3. **CSS specificita problémy** (1,131 `!important`) — střední priorita

**Doporučený postup:**
1. Začít s rozdělením main.py na moduly
2. Implementovat bezpečnostní vylepšení
3. Postupně refaktorovat CSS a JavaScript

**Odhadovaný čas na refaktoring:** 5-7 dní

---

*Report vygenerován automaticky pomocí analýzy kódu.*
