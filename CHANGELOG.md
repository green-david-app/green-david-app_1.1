# Changelog - Green David App

Všechny významné změny v tomto projektu budou dokumentovány v tomto souboru.

Formát je založen na [Keep a Changelog](https://keepachangelog.com/cs/1.0.0/),
a tento projekt dodržuje [Semantic Versioning](https://semver.org/lang/cs/).

---

## [1.0.0] - 2024-12-30

### 🎉 Kompletní refactoring a bezpečnostní vylepšení

### ✅ Přidáno

#### Bezpečnost
- **Validace vstupů**
  - Validace emailu (regex pattern)
  - Validace hodin (rozsah 0-24)
  - Sanitizace názvů souborů
- **Strukturované logování**
  - Logging do souboru (`app.log`)
  - Různé úrovně (INFO, WARNING, ERROR)
  - Rotace logů
- **Konfigurace prostředí**
  - `.env` soubor pro citlivá data
  - `.env.example` jako šablona
  - Validace povinných ENV proměnných v produkci

#### Funkce
- **Error handling**
  - Try-catch bloky kolem všech DB operací
  - Automatický rollback při chybách
  - Konzistentní error responses
- **Database improvements**
  - Foreign key constraints
  - Indexy pro lepší výkon
  - Auto-increment ID
  - Timestamps (created_at, updated_at)

#### Dokumentace
- `README.md` - Kompletní přehled projektu
- `SECURITY.md` - Bezpečnostní checklist
- `DEPLOYMENT.md` - Návod na nasazení
- `CHANGELOG.md` - Historie změn
- API dokumentace v README

### 🔒 Opraveno

#### Kritické bezpečnostní chyby
- ✅ SECRET_KEY validation (vyžadováno v produkci)
- ✅ SQL injection prevence (parametrizované dotazy)
- ✅ Session security (secure, httponly, samesite cookies)
- ✅ Password hashing (bcrypt via Werkzeug)

#### Datová integrita
- ✅ Foreign key cascade delete
- ✅ NOT NULL constraints kde je potřeba
- ✅ Date normalizace (konzistentní YYYY-MM-DD)
- ✅ Validace před INSERT/UPDATE

#### Error handling
- ✅ Graceful degradation při DB chybách
- ✅ Proper HTTP status codes
- ✅ Structured error messages
- ✅ Logging všech errors

### ♻️ Změněno

#### Architektura
- **Reorganizace kódu**
  - Seskupení related funkcí
  - Lepší komentáře a docstringy
  - Konzistentní naming conventions
- **Database schema**
  - Přidány chybějící constraints
  - Indexy pro výkon
  - Normalizace datových typů

#### API
- **Konzistentní responses**
  - Vždy `{"ok": true/false, ...}`
  - Proper error messages
  - HTTP status codes
- **Better validation**
  - Input validation před DB operations
  - Type checking
  - Range validation

### 🗑️ Odstraněno

- ❌ `main.py.bak` (backup soubor)
- ❌ Duplicitní templates
- ❌ Hardcoded credentials
- ❌ Unsafe default values
- ❌ Debug mode v produkci

### 🔧 Technické detaily

#### Dependencies
```
Flask==3.0.0
Werkzeug==3.0.1
gunicorn==21.2.0
openpyxl==3.1.2
```

#### Python Requirements
- Python 3.12+
- pip 23.0+

#### Database Schema Changes
- Přidány indexy: `jobs.date`, `jobs.status`, `timesheets.*`, `calendar_events.date`
- Přidány FK constraints s CASCADE
- Přidány timestamps

---

## [0.9.0] - 2024-12-15 (před refactoringem)

### Původní verze
- Základní CRUD operace
- SQLite databáze
- Flask aplikace
- Jednoduchá autentizace

### Známé problémy (opraveno v 1.0.0)
- ⚠️ Výchozí SECRET_KEY
- ⚠️ Chybějící validace
- ⚠️ Žádné error handling
- ⚠️ Hardcoded credentials
- ⚠️ Chybějící logging

---

## Konvence pro budoucí změny

### Types of changes
- `Added` - Nové funkce
- `Changed` - Změny existujících funkcí
- `Deprecated` - Funkce, které budou brzy odstraněny
- `Removed` - Odstraněné funkce
- `Fixed` - Opravy bugů
- `Security` - Bezpečnostní opravy

### Příklad

```markdown
## [X.Y.Z] - YYYY-MM-DD

### Added
- Nová funkce XYZ (#123)

### Changed
- Změna API endpointu ABC (#456)

### Fixed
- Oprava bugu v modulu DEF (#789)

### Security
- Oprava bezpečnostní chyby (#999)
```

---

## Unreleased

### Plánované pro 1.1.0
- [ ] Rate limiting (Flask-Limiter)
- [ ] CSRF protection (Flask-WTF)
- [ ] Unit tests (pytest)
- [ ] Email notifications
- [ ] PDF export

### Plánované pro 1.2.0
- [ ] PostgreSQL podpora
- [ ] Advanced reporting
- [ ] Multi-tenant
- [ ] Real-time updates

---

[1.0.0]: https://github.com/your-org/green-david-app/releases/tag/v1.0.0
[0.9.0]: https://github.com/your-org/green-david-app/releases/tag/v0.9.0
