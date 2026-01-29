# Green David App 🌿

**Komplexní webová aplikace pro správu stavební/zahradnické firmy**

*A comprehensive web application for construction/landscaping business management*

---

## 🇨🇿 Česky

### O aplikaci

Green David App je moderní Flask webová aplikace navržená pro správu všech aspektů stavební nebo zahradnické firmy:

- **Zakázky** - Kompletní správa projektů s rozpočty, materiály a termíny
- **Zaměstnanci** - Evidence pracovníků, docházky a výkonů  
- **Timesheety** - Sledování odpracovaných hodin
- **Sklad** - Správa materiálů s rezervacemi pro zakázky
- **Plánování** - Denní, týdenní a timeline pohledy
- **Školka rostlin** - Katalog a správa rostlin
- **Finance** - Přehled nákladů a fakturace
- **Reporty** - Exporty do Excelu

### Rychlý start

```bash
# 1. Klonování repozitáře
git clone https://github.com/YOUR_USERNAME/green-david-app.git
cd green-david-app

# 2. Vytvoření virtuálního prostředí
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# nebo: venv\Scripts\activate  # Windows

# 3. Instalace závislostí
pip install -r requirements.txt

# 4. Spuštění aplikace
python main.py

# Aplikace běží na http://localhost:5000
```

### Výchozí přihlašovací údaje

| Uživatel | Heslo | Role |
|----------|-------|------|
| admin | admin | owner |

### Požadavky

- Python 3.9+
- Flask 3.0+
- SQLite (vestavěná databáze)

---

## 🇬🇧 English

### About

Green David App is a modern Flask web application designed for managing all aspects of a construction or landscaping business:

- **Jobs** - Complete project management with budgets, materials and deadlines
- **Employees** - Worker records, attendance and performance tracking
- **Timesheets** - Working hours tracking
- **Warehouse** - Material management with job reservations
- **Planning** - Daily, weekly and timeline views
- **Plant Nursery** - Plant catalog and management
- **Finance** - Cost overview and invoicing
- **Reports** - Excel exports

### Quick Start

```bash
# 1. Clone repository
git clone https://github.com/YOUR_USERNAME/green-david-app.git
cd green-david-app

# 2. Create virtual environment
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# or: venv\Scripts\activate  # Windows

# 3. Install dependencies
pip install -r requirements.txt

# 4. Run application
python main.py

# App runs on http://localhost:5000
```

### Default Login

| Username | Password | Role |
|----------|----------|------|
| admin | admin | owner |

### Requirements

- Python 3.9+
- Flask 3.0+
- SQLite (built-in database)

---

## 🚀 Deployment

### Render.com

Aplikace je připravena pro deployment na Render.com:

1. Vytvořte nový Web Service
2. Připojte GitHub repozitář
3. Nastavte:
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `gunicorn main:app`
4. Přidejte Disk pro perzistentní databázi (`/persistent`)

### Environment Variables

| Proměnná | Popis | Výchozí |
|----------|-------|---------|
| `SECRET_KEY` | Tajný klíč pro sessions | auto-generated |
| `DB_PATH` | Cesta k SQLite databázi | `app.db` |
| `UPLOAD_DIR` | Adresář pro nahrané soubory | `uploads` |

---

## 📱 Mobilní podpora

Aplikace je plně responzivní a optimalizovaná pro mobilní zařízení s:
- Adaptivním layoutem pro všechny velikosti obrazovek
- Touch-friendly ovládacími prvky
- Dolní navigační lištou pro snadný přístup
- PWA-ready strukturou

---

## 📁 Struktura projektu

```
green-david-app/
├── main.py              # Hlavní Flask aplikace
├── wsgi.py              # WSGI entry point
├── requirements.txt     # Python závislosti
├── Dockerfile           # Docker konfigurace
├── Procfile             # Render/Heroku konfigurace
├── static/              # CSS, JS, obrázky
│   ├── style.css
│   ├── js/
│   └── img/
├── templates/           # HTML šablony (Jinja2)
├── *.html               # Hlavní stránky aplikace
└── migrations/          # SQL migrace
```

---

## 🔧 API Endpoints

Aplikace poskytuje REST API pro všechny moduly:

- `/api/jobs` - CRUD operace pro zakázky
- `/api/employees` - Správa zaměstnanců
- `/api/timesheets` - Docházka
- `/api/warehouse` - Sklad materiálů
- `/api/planning` - Plánování
- `/api/nursery` - Školka rostlin

---

## 📝 License

MIT License - volně použitelné pro komerční i nekomerční účely.

---

## 👨‍💻 Autor

Green David s.r.o. - Příbram, Česká republika

---

*Vytvořeno s ❤️ pro české stavební a zahradnické firmy*
