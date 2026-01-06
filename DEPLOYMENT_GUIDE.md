# Návod na nahrání do GitHubu a deployment na Render

## Krok 1: Nahrání do GitHubu

### A) Pokud máš už GitHub repozitář:

```bash
cd /cesta/k/green-david-WORK
git remote -v  # Zkontroluj, že máš správný remote
git push origin main
```

### B) Pokud NEMÁŠ ještě GitHub repozitář:

1. Jdi na GitHub.com a vytvoř nový repozitář (zelené tlačítko "New")
2. Pojmenuj ho např. "green-david-app"
3. NEVOLEJ "Initialize with README" (už máme soubory)
4. Po vytvoření ti GitHub ukáže příkazy - použij tyto:

```bash
cd /cesta/k/green-david-WORK
git remote add origin https://github.com/TVOJE_USERNAME/green-david-app.git
git push -u origin main
```

## Krok 2: Deployment na Render.com

1. Jdi na https://render.com a přihlaš se
2. Klikni na "New +" → "Web Service"
3. Připoj svůj GitHub účet (pokud ještě není)
4. Vyber repozitář "green-david-app"
5. Nastav následující:

### Základní nastavení:
- **Name**: green-david-app (nebo jak chceš)
- **Region**: Frankfurt (EU) - nejblíže k ČR
- **Branch**: main
- **Runtime**: Python 3
- **Build Command**: `pip install -r requirements.txt`
- **Start Command**: `gunicorn -w 4 -b 0.0.0.0:$PORT main:app`

### Environment Variables (DŮLEŽITÉ!):
Klikni na "Add Environment Variable" a přidej:

```
SECRET_KEY = [vygeneruj náhodný string, např. použij: python -c "import os; print(os.urandom(32).hex())"]
DB_PATH = /tmp/app.db
RENDER = true
```

### Instance Type:
- **Free** (pro testování)
- **Starter** ($7/měsíc - pro produkční použití s lepším výkonem)

6. Klikni "Create Web Service"

## Krok 3: První spuštění

Po deploymentu (trvá 2-5 minut):

1. Render ti dá URL jako: `https://green-david-app.onrender.com`
2. Otevři URL v prohlížeči
3. **DŮLEŽITÉ**: První spuštění vytvoří databázi - může trvat 30-60 sekund
4. Aplikace by měla běžet!

## Důležité poznámky:

### ⚠️ Databáze na Free plánu:
- Na FREE plánu se databáze resetuje po 15 minutách nečinnosti
- Pro trvalou databázi potřebuješ:
  - Buď **Starter plán** ($7/měsíc)
  - Nebo přidat **Persistent Disk** k Free plánu ($1/měsíc za 1GB)

### Persistent Disk (pro zachování dat):
1. V Render Dashboard → Tvoje služba → Settings
2. Scroll dolů na "Disks"
3. Klikni "Add Disk"
4. Mount Path: `/persistent`
5. Size: 1 GB
6. V Environment Variables změň: `DB_PATH=/persistent/app.db`

### Automatické updaty:
- Každý `git push` na GitHub spustí nový deployment
- Build trvá 2-5 minut
- Render ti pošle email když je hotovo

## Řešení problémů:

### Aplikace nejde načíst:
1. V Render Dashboard → tvoje služba → "Logs"
2. Podívej se na chybové hlášky
3. Nejčastější problémy:
   - Chybí environment proměnné
   - Špatný START command
   - Chyba v kódu

### Databáze je prázdná:
- Je potřeba vytvořit admina ručně nebo importovat data
- Můžeš použít script pro inicializaci

### Timeout při načítání:
- Free plán "usíná" po 15 minutách
- První request po probuzení trvá 30-60 sekund

## Kontakt a podpora:
- Render dokumentace: https://render.com/docs
- Flask dokumentace: https://flask.palletsprojects.com/
