# Green David App - PLNĚ OPRAVENÁ VERZE

## Co bylo rozbité

ChatGPT ti rozbil několik věcí:

1. ❌ `host="0.0.0.0"` - způsobovalo problémy na Macu v Safari
2. ❌ `@app.get()` místo `@app.route()` - Python syntax error
3. ❌ Nedokončený řádek v `page_job_detail_query()` funkci
4. ❌ Zbytečná závorka `jid)` uprostřed souboru
5. ❌ Nová type hint syntax `str | None` - nefunguje v Python 3.9

## Co je opraveno

✅ Automatická detekce prostředí (lokál vs Render)
✅ Správné Flask dekorátory `@app.route()`
✅ Kompletní funkce bez syntax chyb
✅ Kompatibilní s Python 3.9+ (tvoje verze: 3.9)
✅ Python syntax validována

## JAK TO SPUSTIT - KROK ZA KROKEM

### 1. Otevři terminál

```bash
# Přejdi do složky s projektem
cd /Users/greendavid/Desktop/green-david-WORK

# Smaz starý main.py a nahraď ho opraveným z ZIPu
# (nebo rozbal celý ZIP do nové složky)
```

### 2. Zkontroluj Python

```bash
# Zjisti jakou verzi Python máš
python3 --version

# Mělo by vrátit něco jako: Python 3.x.x
```

### 3. Deaktivuj venv (pokud je aktivní)

```bash
deactivate
```

### 4. Spusť aplikaci

```bash
python3 main.py
```

### 5. Co uvidíš v terminálu (správný výstup)

```
[DB] Using database: app.db
[Server] Starting Flask app on 127.0.0.1:5000 (debug=True)
 * Serving Flask app 'main'
 * Debug mode: on
WARNING: This is a development server. Do not use it in a production deployment.
 * Running on http://127.0.0.1:5000
Press CTRL+C to quit
```

### 6. Otevři aplikaci v Safari

**NEPOUŽÍVEJ** command+click na link v terminálu!

Místo toho:

1. Otevři Safari **ručně**
2. Do adresního řádku napiš **přesně**:
   ```
   127.0.0.1:5000
   ```
   nebo
   ```
   localhost:5000
   ```

**DŮLEŽITÉ:** 
- ❌ NEPIŠ "www." na začátku
- ❌ NEPIŠ "http://" na začátku (Safari to doplní samo)
- ✅ Jen prostě: `127.0.0.1:5000`

## Řešení problémů

### ❌ "Permission denied: python"

Použij `python3` místo `python`:
```bash
python3 main.py
```

### ❌ "SyntaxError: invalid syntax"

Ujisti se, že používáš OPRAVENOU verzi main.py z tohoto ZIPu!

### ❌ "Port 5000 already in use"

```bash
# Zjisti co běží na portu 5000
lsof -ti:5000

# Ukonči ten proces
kill -9 $(lsof -ti:5000)

# Nebo použij jiný port
PORT=5001 python3 main.py
```

### ❌ Safari stále zobrazuje "www.127.0.0.1:5000"

1. Zavři Safari úplně (⌘Q)
2. Otevři Safari znovu
3. Vymaž historii/cache (⌘⇧R nebo Command+Shift+Delete)
4. Zkus Incognito mode (⌘⇧N)
5. Nebo zkus Chrome/Firefox

## Jak vypnout server

V terminálu stiskni: **CTRL+C**

## Test že vše funguje

Po spuštění by měl terminál vypadat takto:

```
(venv) greendavid@green-MBP green-david-WORK % python3 main.py
[DB] Using database: app.db
[Server] Starting Flask app on 127.0.0.1:5000 (debug=True)
 * Serving Flask app 'main'
 * Debug mode: on
 * Running on http://127.0.0.1:5000
Press CTRL+C to quit
 * Restarting with stat
 * Debugger is active!
```

A Safari by měl zobrazit tvou přihlašovací stránku aplikace.

## Deployment na Render zůstává stejný

Aplikace automaticky detekuje Render prostředí, takže:
- Na Render použije `0.0.0.0` (veřejný přístup)
- Lokálně použije `127.0.0.1` (localhost)
- Není třeba nic měnit!
