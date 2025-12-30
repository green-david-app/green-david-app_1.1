# Deployment Guide - Green David App

## 🚀 Lokální vývoj

### 1. Naklonování a instalace

```bash
# Naklonovat repozitář
git clone https://github.com/your-org/green-david-app.git
cd green-david-app

# Vytvořit virtuální prostředí
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# nebo
venv\Scripts\activate  # Windows

# Instalovat závislosti
pip install -r requirements.txt

# Vytvořit .env z šablony
cp .env.example .env

# Upravit .env (nastavit SECRET_KEY, admin credentials)
nano .env
```

### 2. Spuštění

```bash
# Development server
export FLASK_ENV=development
python main.py

# Aplikace běží na http://localhost:5000
```

### 3. První přihlášení

1. Otevřít http://localhost:5000
2. Přihlásit se s admin credentials z .env
3. **OKAMŽITĚ změnit admin heslo!**

---

## 🌐 Produkční nasazení (Render.com)

### Příprava

1. **Push do GitHub**
   ```bash
   git add .
   git commit -m "Ready for deployment"
   git push origin main
   ```

2. **Vytvořit účet na Render.com**
   - https://render.com
   - Propojit s GitHub účtem

### Konfigurace Web Service

1. **New → Web Service**
   - Repository: Vybrat váš repozitář
   - Name: `green-david-app`
   - Environment: `Python 3`
   - Region: `Frankfurt` (nejblíž k ČR)
   - Branch: `main`

2. **Build Command:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Start Command:**
   ```bash
   gunicorn -w 4 -b 0.0.0.0:$PORT main:app
   ```

4. **Environment Variables (⚠️ DŮLEŽITÉ):**
   ```
   SECRET_KEY = <vygenerovaný tajný klíč>
   FLASK_ENV = production
   ADMIN_EMAIL = admin@greendavid.cz
   ADMIN_PASSWORD = <silné heslo>
   DB_PATH = /opt/render/project/data/app.db
   UPLOAD_DIR = /opt/render/project/data/uploads
   ```

5. **Disk pro perzistentní data:**
   - Add Disk
   - Name: `data`
   - Mount Path: `/opt/render/project/data`
   - Size: `1 GB` (nebo dle potřeby)

6. **Deploy!**

### Po nasazení

1. ✅ Otevřít aplikaci na Render URL
2. ✅ Přihlásit se jako admin
3. ✅ Změnit admin heslo
4. ✅ Zkontrolovat logs
5. ✅ Otestovat hlavní funkce

---

## 🐳 Docker (alternativa)

### Dockerfile

```dockerfile
FROM python:3.12-slim

WORKDIR /app

# Závislosti
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Kód aplikace
COPY . .

# Vytvořit adresáře
RUN mkdir -p uploads logs data

EXPOSE 5000

CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5000", "main:app"]
```

### Docker Compose

```yaml
version: '3.8'

services:
  app:
    build: .
    ports:
      - "5000:5000"
    environment:
      - SECRET_KEY=${SECRET_KEY}
      - FLASK_ENV=production
      - ADMIN_EMAIL=${ADMIN_EMAIL}
      - ADMIN_PASSWORD=${ADMIN_PASSWORD}
    volumes:
      - ./data:/app/data
      - ./uploads:/app/uploads
      - ./logs:/app/logs
    restart: unless-stopped
```

### Spuštění

```bash
# Build
docker-compose build

# Start
docker-compose up -d

# Logs
docker-compose logs -f

# Stop
docker-compose down
```

---

## 📊 Monitoring a údržba

### Logs

**Render.com:**
- Dashboard → Logs tab
- Nebo CLI: `render logs -t green-david-app`

**Lokálně:**
```bash
tail -f app.log
```

### Zálohování databáze

**Automatické (doporučeno):**

Vytvořit skript `backup.sh`:
```bash
#!/bin/bash
DATE=$(date +%Y%m%d-%H%M%S)
cp /opt/render/project/data/app.db /opt/render/project/data/backups/app-$DATE.db

# Ponechat pouze posledních 7 záloh
cd /opt/render/project/data/backups
ls -t | tail -n +8 | xargs -r rm
```

**Manuální:**
```bash
# Stáhnout DB z Renderu
render disk download data app.db

# Nebo přes SSH
scp user@server:/path/to/app.db ./backup-$(date +%Y%m%d).db
```

### Aktualizace

```bash
# 1. Lokálně otestovat změny
git pull
pip install -r requirements.txt
python main.py

# 2. Commit a push
git add .
git commit -m "Update: feature XYZ"
git push

# 3. Render automaticky přenasadí
# (můžete sledovat v Dashboard → Deployments)
```

---

## 🔧 Troubleshooting

### Aplikace nefunguje po nasazení

```bash
# 1. Zkontrolovat logs
render logs -t green-david-app

# 2. Ověřit ENV variables
render env -t green-david-app

# 3. Zkontrolovat disk
render disk list
```

### Databázové chyby

```bash
# Připojit se přes SSH (pokud dostupné)
# nebo stáhnout DB a zkontrolovat lokálně

sqlite3 app.db "PRAGMA integrity_check;"
```

### Vysoké využití paměti

```bash
# Zkontrolovat velikost DB
du -h /opt/render/project/data/app.db

# Zvážit zvýšení worker count nebo upgrade plánu
```

---

## 📞 Podpora

- **Dokumentace Render:** https://render.com/docs
- **Flask dokumentace:** https://flask.palletsprojects.com/
- **GitHub Issues:** Pro reportování bugů

---

## 📝 Changelog

### v1.0.0 (2024-12-30)
- ✅ Bezpečnostní vylepšení
- ✅ Validace vstupů
- ✅ Strukturované logování
- ✅ Error handling
- ✅ Production-ready konfigurace
