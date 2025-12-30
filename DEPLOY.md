# Deployment na Render.com

## Krok 1: Push na GitHub

```bash
cd green-david-app-redesigned

# Pokud ještě není git repo, inicializuj:
git init
git add .
git commit -m "iOS minimalist redesign - complete rewrite"

# Přidej remote (nahraď URL svým repozitářem):
git remote add origin https://github.com/TVUJ_USERNAME/TVUJ_REPO.git

# Push (pokud nahrazuješ existující repo, použij --force):
git push -u origin main
# nebo
git push -u origin master --force
```

## Krok 2: Deploy na Render

1. Jdi na [render.com](https://render.com)
2. Klikni na **"New +"** → **"Web Service"**
3. Spoj se svým GitHub repozitářem
4. Render automaticky detekuje:
   - **Build Command**: (prázdné, nebo `pip install -r requirements.txt`)
   - **Start Command**: Detekuje z `Procfile`: `gunicorn --workers 2 --threads 4 --timeout 120 --bind 0.0.0.0:$PORT wsgi:app`

## Krok 3: Environment Variables (volitelné)

V Render dashboardu můžeš nastavit:
- `ADMIN_EMAIL` - výchozí: `admin@greendavid.local`
- `ADMIN_PASSWORD` - výchozí: `admin123`
- `SECRET_KEY` - automaticky generováno
- `DB_PATH` - výchozí: `app.db`

## Poznámky

- Render automaticky používá `$PORT` z prostředí
- Databáze se vytvoří automaticky při prvním spuštění
- Admin účet se vytvoří automaticky pokud neexistuje

