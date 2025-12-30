# 🌿 Green David App - Firemní Systém

> Moderní webová aplikace pro správu zakázek, zaměstnanců, výkazů hodin a kalendáře.

![Python](https://img.shields.io/badge/python-3.12-blue)
![Flask](https://img.shields.io/badge/flask-3.0-green)
![License](https://img.shields.io/badge/license-Proprietary-red)

---

## ✨ Funkce

- 📋 **Správa zakázek** - Kompletní evidence zakázek s materiálem a nářadím
- 👥 **Zaměstnanci** - Evidence zaměstnanců a brigádníků
- ⏰ **Výkazy hodin** - Sledování odpracovaných hodin
- 📅 **Kalendář** - Plánování událostí a deadlinů
- 📊 **Reporting** - Export do CSV/XLSX
- 🔐 **Bezpečnost** - Role-based přístup, šifrovaná hesla
- 📱 **Responzivní** - Funguje na mobilu i desktopu

---

## 🚀 Rychlý start

### Předpoklady

- Python 3.12+
- pip
- Git

### Instalace

```bash
# 1. Klonovat repozitář
git clone https://github.com/your-org/green-david-app.git
cd green-david-app

# 2. Vytvořit virtuální prostředí
python3 -m venv venv
source venv/bin/activate

# 3. Instalovat závislosti
pip install -r requirements.txt

# 4. Nakonfigurovat
cp .env.example .env
# Upravit .env (nastavit SECRET_KEY!)

# 5. Spustit
python main.py
```

**Výchozí přihlášení:**
- Email: `admin@greendavid.local`
- Heslo: `admin123`
- ⚠️ **ZMĚŇTE OKAMŽITĚ po přihlášení!**

---

## 📚 Dokumentace

- [🔒 Bezpečnost](SECURITY.md) - Bezpečnostní checklist a best practices
- [🚀 Deployment](DEPLOYMENT.md) - Návod na nasazení do produkce
- [🔧 API Reference](#api-reference) - Dokumentace API endpointů

---

## 🏗️ Architektura

```
green-david-app/
├── main.py              # Hlavní aplikace (Flask)
├── requirements.txt     # Python závislosti
├── .env.example         # Šablona konfigurace
├── app.db              # SQLite databáze (vytvořena automaticky)
├── uploads/            # Nahrané soubory
├── app.log             # Aplikační logy
├── static/             # Statické soubory (CSS, JS, obrázky)
│   ├── css/
│   └── js/
└── templates/          # HTML šablony (pokud používáte)
```

### Technologie

- **Backend:** Flask 3.0, Python 3.12
- **Databáze:** SQLite (pro jednoduchost, lze upgradovat na PostgreSQL)
- **Auth:** Werkzeug password hashing, session-based
- **Frontend:** Vanilla JavaScript, Bootstrap-like custom CSS
- **Deployment:** Gunicorn, Render.com (nebo Docker)

---

## 🔐 Bezpečnost

### ✅ Implementováno

- ✅ Password hashing (bcrypt)
- ✅ Session security (secure cookies)
- ✅ SQL injection protection (parametrizované dotazy)
- ✅ Input validation
- ✅ Role-based access control (admin/manager/worker)
- ✅ Error handling a logging
- ✅ Environment-based configuration

### 🔧 Doporučeno přidat

- [ ] Rate limiting (Flask-Limiter)
- [ ] CSRF protection (Flask-WTF)
- [ ] 2FA autentizace
- [ ] API rate limiting
- [ ] Audit logging

➡️ **Více v [SECURITY.md](SECURITY.md)**

---

## 📊 API Reference

### Autentizace

```http
POST /api/login
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "password"
}

Response: { "ok": true }
```

```http
POST /api/logout

Response: { "ok": true }
```

```http
GET /api/me

Response: {
  "ok": true,
  "authenticated": true,
  "user": { "id": 1, "email": "...", "role": "admin" }
}
```

### Zaměstnanci

```http
GET /api/employees
Response: { "ok": true, "employees": [...] }

POST /api/employees
{ "name": "Jan Novák", "role": "Zahradník" }

PATCH /api/employees
{ "id": 1, "name": "Jan Novák" }

DELETE /api/employees?id=1
```

### Zakázky

```http
GET /api/jobs
Response: { "ok": true, "jobs": [...] }

POST /api/jobs
{
  "title": "Zakázka XY",
  "client": "Firma s.r.o.",
  "city": "Praha",
  "code": "2024-001",
  "date": "2024-12-30",
  "status": "Plán"
}

GET /api/jobs/{id}
Response: { "ok": true, "job": {...}, "materials": [...], "tools": [...] }

PATCH /api/jobs
{ "id": 1, "status": "Probíhá" }

DELETE /api/jobs?id=1
```

### Výkazy hodin

```http
GET /api/timesheets?from=2024-12-01&to=2024-12-31&employee_id=1
Response: { "ok": true, "rows": [...] }

POST /api/timesheets
{
  "employee_id": 1,
  "job_id": 1,
  "date": "2024-12-30",
  "hours": 8.0,
  "place": "Praha 6",
  "activity": "Montáž plotu"
}

PATCH /api/timesheets
{ "id": 1, "hours": 8.5 }

DELETE /api/timesheets?id=1

GET /api/timesheets/export?from=2024-12-01&to=2024-12-31
Response: CSV file download
```

### Úkoly

```http
GET /api/tasks?job_id=1
Response: { "ok": true, "tasks": [...] }

POST /api/tasks
{
  "title": "Objednat materiál",
  "description": "Cement 10 pytlů",
  "job_id": 1,
  "employee_id": 2,
  "due_date": "2024-12-31",
  "status": "open"
}

PATCH /api/tasks
{ "id": 1, "status": "hotovo" }

DELETE /api/tasks?id=1
```

---

## 🧪 Testování

```bash
# TODO: Přidat unit testy
# pytest tests/
```

---

## 📈 Roadmap

### v1.1 (Q1 2025)
- [ ] Unit testy
- [ ] Rate limiting
- [ ] CSRF protection
- [ ] Email notifikace
- [ ] PDF reporty

### v1.2 (Q2 2025)
- [ ] Mobile app
- [ ] Push notifikace
- [ ] Advanced reporting
- [ ] Multi-tenant support

### v2.0 (Q3 2025)
- [ ] Migrate to PostgreSQL
- [ ] GraphQL API
- [ ] Real-time updates (WebSockets)
- [ ] AI asistent

---

## 🤝 Contributing

Toto je proprietární software pro Green David s.r.o.

Pro interní přispěvatele:

1. Fork repozitář
2. Vytvořit feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit změny (`git commit -m 'Add some AmazingFeature'`)
4. Push do branch (`git push origin feature/AmazingFeature`)
5. Otevřít Pull Request

---

## 📝 License

© 2024 Green David s.r.o. - All Rights Reserved

Tento software je proprietární a důvěrný. Neautorizované kopírování,
distribuce nebo modifikace tohoto softwaru je přísně zakázána.

---

## 👥 Tým

- **Vývoj:** Váš tým
- **Design:** Váš tým
- **Podpora:** support@greendavid.cz

---

## 📞 Kontakt

**Green David s.r.o.**
- 🌐 Website: https://greendavid.cz
- 📧 Email: info@greendavid.cz
- 🐛 Bug reports: GitHub Issues (interní)

---

<div align="center">
Made with ❤️ by Green David Team
</div>
