# Green David App - Kompletní instalace ✅

## JAK NAINSTALOVAT:

### 1. Rozbal ZIP
```bash
# Rozbal green-david-COMPLETE.zip na plochu
# Měl bys mít složku: /Users/greendavid/Desktop/green-david-COMPLETE
```

### 2. Přejmenuj složky
```bash
cd /Users/greendavid/Desktop

# Záloha staré verze (pokud chceš)
mv green-david-WORK green-david-WORK-backup

# Přejmenuj novou verzi
mv green-david-COMPLETE green-david-WORK
```

### 3. Spusť aplikaci
```bash
cd /Users/greendavid/Desktop/green-david-WORK
python3 main.py
```

### 4. Otevři v prohlížeči
```
http://127.0.0.1:5000
```

### 5. Přihlaš se
```
Email: david@test.cz
Heslo: test123
```

## CO JE NOVÉHO:

✅ **Issues** - kompletně funkční systém pro hlášení problémů/překážek
✅ **Delegování** - issues se automaticky zobrazují přiřazeným zaměstnancům
✅ **Integrace** - propojení mezi Zakázky → Issues → Úkoly
✅ **Python 3.9 kompatibilita** - vše funguje s tvým Pythonem

## STRUKTURA:

```
green-david-WORK/
├── main.py              ← Backend (API)
├── app.db              ← Databáze (s issues tabulkou)
├── index.html          ← Dashboard
├── jobs.html           ← Zakázky (s Issues sekcí)
├── issues.html         ← Samostatná stránka Issues
├── tasks.html          ← Úkoly (s Moje Issues)
├── employees.html      ← Zaměstnanci
├── warehouse.html      ← Sklad
├── finance.html        ← Finance
├── static/
│   ├── style.css
│   ├── bottom-nav.js
│   ├── js/
│   │   └── jobs-issues.js
│   └── css/
│       └── app.css
└── migrations/
    └── (SQL migrace)
```

## POKUD NĚCO NEJDE:

### Chyba: "Permission denied: python"
```bash
python3 main.py  # Použij python3 místo python
```

### Chyba: "No module named 'flask'"
```bash
pip3 install flask==3.0.0 werkzeug==2.3.7
```

### Aplikace neběží
```bash
# Zastav všechny Python procesy
pkill -9 python3

# Spusť znovu
python3 main.py
```

### 404 na static soubory
Ujisti se že máš správnou strukturu složek - static/ musí být přímo v green-david-WORK/

## DATABÁZE:

Issues tabulka je **již vytvořená** v app.db! Nemusíš spouštět žádné migrace.

## PŘIHLAŠOVACÍ ÚDAJE:

```
david@test.cz / test123
admin@greendavid.local / admin123
```

## HOTOVO! 🎉
