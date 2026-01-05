# Green David App - Opravená verze

## Co bylo opraveno

ChatGPT nastavil `host="0.0.0.0"` v `main.py`, což je správné pro Render.com, ale na Macu to může způsobovat problémy s lokálním vývojem.

**Oprava:**
- Aplikace teď automaticky detekuje prostředí
- **Lokálně** (na tvém Macu): používá `127.0.0.1` (localhost)
- **Na Render.com**: používá `0.0.0.0` (veřejný přístup)
- Debug mode je automaticky zapnutý jen lokálně

## Jak spustit aplikaci

### 1. Přes terminál (doporučeno)

```bash
# Přejdi do složky projektu
cd /cesta/k/green-david-fixed

# Aktivuj virtuální prostředí (pokud máš)
source venv/bin/activate

# Spusť aplikace
python main.py
```

Aplikace poběží na: **http://127.0.0.1:5000**

### 2. Zkontroluj startup log

Po spuštění uvidíš:
```
[DB] Using database: app.db
[Server] Starting Flask app on 127.0.0.1:5000 (debug=True)
 * Running on http://127.0.0.1:5000
```

### 3. Otevři v prohlížeči

```
http://127.0.0.1:5000
```

nebo

```
http://localhost:5000
```

## Řešení problémů

### Port už je používaný
Pokud dostaneš chybu "Address already in use":
```bash
# Najdi proces na portu 5000
lsof -ti:5000

# Zabiješ ho
kill -9 $(lsof -ti:5000)

# Nebo použij jiný port
PORT=5001 python main.py
```

### Databáze nenalezena
Aplikace automaticky vytvoří `app.db` v hlavní složce projektu.

### Safari/Chrome nefunguje správně
1. Vymaž cache prohlížeče
2. Použij InPrivate/Incognito mode
3. Zkus Firefox jako alternativu

## Konfigurace databáze

Aplikace automaticky detekuje prostředí:

- **Lokálně**: `app.db` (v kořenové složce projektu)
- **Render.com s persistent diskem**: `/persistent/app.db`
- **Render.com bez persistent disku**: `/tmp/app.db`
- **Custom cesta**: nastav environment variable `DB_PATH`

## Deployment na Render.com

Není třeba nic měnit! Aplikace automaticky detekuje Render prostředí a použije správnou konfiguraci:
- Host: `0.0.0.0`
- Port: z `$PORT` environment variable
- Debug: `False` (vypnutý)

Gunicorn konfigurace v `Procfile` zůstává:
```
web: gunicorn -w 4 -b 0.0.0.0:8000 main:app
```
