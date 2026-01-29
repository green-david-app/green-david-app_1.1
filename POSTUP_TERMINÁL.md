# 🚀 POSTUP - JAK SPUSTIT NA LOCALHOSTU PŘES TERMINÁL

## Krok 1: Stáhni a rozbal

1. Stáhni soubor: `green-david-READY.zip`
2. Rozbal ho někam na disk, například:
   - Mac: `~/Desktop/green-david/`
   - Windows: `C:\Users\David\Desktop\green-david\`

---

## Krok 2: Otevři Terminál

### 🍎 Mac:
**Možnost A - Přes Finder:**
1. Otevři Finder
2. Najdi složku `green-david-FINAL`
3. Pravé tlačítko na složku
4. Vyber "Services" → "New Terminal at Folder"

**Možnost B - Manuálně:**
1. Otevři aplikaci "Terminal" (cmd+mezerník → napiš "terminal")
2. Napiš:
```bash
cd ~/Desktop/green-david/green-david-FINAL
```
(uprav cestu podle toho, kam jsi rozbalil)

### 🪟 Windows:
**Možnost A - Přes Explorer:**
1. Otevři Explorer (Win+E)
2. Najdi složku `green-david-FINAL`
3. Klikni do **adresního řádku nahoře** (kde je cesta)
4. Napiš `cmd` a zmáčkni Enter

**Možnost B - Manuálně:**
1. Win+R → napiš `cmd` → Enter
2. Napiš:
```cmd
cd C:\Users\David\Desktop\green-david\green-david-FINAL
```
(uprav cestu podle toho, kam jsi rozbalil)

---

## Krok 3: Ověř, že jsi ve správné složce

Napiš:
```bash
ls
```
(na Windows: `dir`)

**Měl bys vidět:**
```
README.md
TEST_CHECKLIST.md
main.py
warehouse_extended.py
planning_extended_api.py
warehouse.html
start_local.sh
start_local.bat
static/
```

✅ Pokud vidíš tyto soubory, jsi na správném místě!

---

## Krok 4: Spusť aplikaci

### 🍎 Mac:
```bash
./start_local.sh
```

**Pokud dostaneš "Permission denied":**
```bash
chmod +x start_local.sh
./start_local.sh
```

### 🪟 Windows:
```cmd
start_local.bat
```

**NEBO univerzálně (Mac i Windows):**
```bash
python3 main.py
```
(na Windows může být jen `python` místo `python3`)

---

## Krok 5: Počkej na start

Uvidíš něco jako:

```
✅ Python3 nalezen: Python 3.11.0
✅ Flask nainstalován

📊 Nastavení:
   Admin email: admin@greendavid.local
   Admin heslo: admin123
   Databáze: ./app.db

🌐 Server poběží na: http://127.0.0.1:5000

⚠️  Pro zastavení serveru zmáčkni CTRL+C

──────────────────────────────────────────────────────────

[DB] Using database: ./app.db
[DB] Created directory: .
✅ Warehouse Extended migrations applied
✅ Planning Extended Routes loaded
✅ Warehouse Extended Routes loaded
[Server] Starting Flask app on 127.0.0.1:5000 (debug=True)
 * Serving Flask app 'main'
 * Debug mode: on
 * Running on http://127.0.0.1:5000
```

✅ **Když vidíš "Running on http://127.0.0.1:5000" - server běží!**

---

## Krok 6: Otevři v prohlížeči

1. Otevři **Safari, Chrome, nebo Firefox**
2. V adresním řádku napiš:
```
http://127.0.0.1:5000
```
3. Zmáčkni Enter

---

## Krok 7: Přihlaš se

```
Email: admin@greendavid.local
Heslo: admin123
```

✅ **Měl bys být přihlášený!**

---

## Krok 8: Otevři Sklad

V menu najdi **"Sklad"** nebo přejdi na:
```
http://127.0.0.1:5000/warehouse.html
```

✅ **Měl bys vidět:**
- Statistiky nahoře (0 hodnota, 0 položek atd.)
- 5 tabů: 📦 Položky, 📍 Lokace, 📋 Pohyby, 🔒 Rezervace, ✅ Inventura

---

## Krok 9: Otestuj funkce

Postupuj podle souboru **`TEST_CHECKLIST.md`**

Ten tě provede krok za krokem:
1. Vytvoření lokací
2. Přidání položky s lokací
3. Vytvoření zakázky
4. Výdej na zakázku
5. Vrácení materiálu
6. Rezervace
7. Inventura
8. Sloučení položek
... a další

---

## 🛑 Jak zastavit server

V terminálu zmáčkni: **CTRL+C**

```
^C
Shutting down...
```

---

## 🔄 Jak restartovat

Prostě znovu spusť:
```bash
./start_local.sh
```

---

## ✅ KONTROLNÍ CHECKLIST

Po startu zkontroluj:

**V terminálu vidíš:**
- [ ] ✅ Python3 nalezen
- [ ] ✅ Flask nainstalován
- [ ] ✅ Warehouse Extended migrations applied
- [ ] ✅ Warehouse Extended Routes loaded
- [ ] Running on http://127.0.0.1:5000

**V prohlížeči:**
- [ ] Otevřel se login screen
- [ ] Přihlásil ses s admin/admin123
- [ ] Vidíš dashboard
- [ ] V menu je "Sklad"
- [ ] Sklad se otevře na /warehouse.html
- [ ] Vidíš 5 tabů
- [ ] Statistiky se zobrazují (i když jsou 0)

✅ Pokud všechno funguje, pokračuj v TEST_CHECKLIST.md!

---

## 🐛 Nejčastější problémy

### ❌ "python3: command not found"
**Řešení:** Nainstaluj Python3
- Mac: https://www.python.org/downloads/
- Nebo přes Homebrew: `brew install python3`

### ❌ "ModuleNotFoundError: No module named 'flask'"
**Řešení:**
```bash
pip3 install flask
```
Nebo:
```bash
pip3 install flask --break-system-packages
```

### ❌ "Permission denied: ./start_local.sh"
**Řešení:**
```bash
chmod +x start_local.sh
./start_local.sh
```

### ❌ "Address already in use"
**Řešení:** Port 5000 je obsazený. Změň port:
```bash
export PORT=5001
python3 main.py
```
Pak otevři: `http://127.0.0.1:5001`

### ❌ Přihlášení nefunguje
**Řešení:** 
1. Zkontroluj terminál, měl bys vidět:
   ```
   [DB] Auto-upgraded admin@greendavid.local to owner role
   ```
2. Pokud ne, smaž databázi a spusť znovu:
   ```bash
   rm app.db
   ./start_local.sh
   ```

### ❌ Warehouse tab je prázdný
**Řešení:**
1. Otevři konzoli prohlížeče (F12)
2. Podívej se na chyby v "Console"
3. Zkontroluj, že složka `static/warehouse/` existuje
4. Zkontroluj, že v ní jsou soubory: items.js, movements.js, locations.js, reservations.js, inventory.js

---

## 📞 Stále nefunguje?

1. Zkopíruj celý výpis z terminálu
2. Otevři konzoli prohlížeče (F12) → záložka "Console"
3. Zkopíruj všechny červené chyby
4. Pošli mi obojí

---

## ✨ Hotovo!

Pokud vše funguje, máš nyní běžící **Green David Warehouse Extended** na localhostu!

🎯 **Další krok:** Postupuj podle **TEST_CHECKLIST.md** pro kompletní test všech funkcí.

**Užij si! 🚀**
