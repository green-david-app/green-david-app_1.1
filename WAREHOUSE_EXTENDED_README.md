# 🎉 GREEN DAVID - WAREHOUSE EXTENDED (FINÁLNÍ VERZE)

## ✅ CO JE NOVÉHO

Tvá **plně funkční aplikace** s integrovaným **Warehouse Extended**!

### Nové funkce skladu:
- 📍 Skladové lokace (hierarchie Sklad-Regál-Police)
- 🔗 Přiřazování materiálu k zakázkám
- ↩️ Vracení materiálu ze stavby
- 🔒 Rezervace materiálu
- 📅 Expirační datumy & Čísla šarží
- 🔀 Slučování duplicitních položek
- ✏️ Přejmenování položek
- ✅ Inventurní režim s auto-korekcemi
- 📊 Real-time statistiky

---

## 🚀 INSTALACE (3 KROKY)

### 1. Rozbal ZIP

Rozbal `green-david-WORK-WAREHOUSE-EXTENDED.zip` na plochu nebo jinam:
```
~/Desktop/green-david-WORK/
```

### 2. Otevři terminál

**Mac:**
- Finder → Najdi složku `green-david-WORK`
- Pravé tlačítko → "Services" → "New Terminal at Folder"

**Nebo manuálně:**
```bash
cd ~/Desktop/green-david-WORK
```

### 3. Spusť

```bash
python3 main.py
```

---

## 🌐 OTEVŘI V PROHLÍŽEČI

```
http://127.0.0.1:5000
```

**Přihlášení:**
- Email: `david@greendavid.cz`
- Heslo: *(tvé současné heslo)*

---

## ✅ KONTROLA PO SPUŠTĚNÍ

V terminálu **MUSÍŠ** vidět:

```
✅ Jobs Extended API loaded
✅ Planning Module loaded
✅ Planning Extended Routes loaded
✅ Warehouse Extended migrations applied    ← TOHLE!
✅ Warehouse Extended Routes loaded         ← TOHLE!
[Server] Starting Flask app on 127.0.0.1:5000
```

**Pokud vidíš obě "Warehouse Extended" hlášky = FUNGUJE! 🎉**

---

## 🎯 OTESTUJ SKLAD

1. **Přihlaš se**
2. **Otevři Sklad** (v menu nebo `/warehouse.html`)
3. **Měl bys vidět:**
   - ✅ Statistiky nahoře (6 boxů)
   - ✅ 5 tabů: 📦 Položky, 📍 Lokace, 📋 Pohyby, 🔒 Rezervace, ✅ Inventura
   - ✅ Tmavý design (ne modré pozadí!)

---

## 📋 RYCHLÝ TEST FUNKCÍ

### Test 1: Vytvoř lokaci
1. Tab "📍 Lokace"
2. "+ Nová lokace"
3. Kód: `A-1-B`, Název: `Sklad A, Regál 1, Police B`
4. Uložit

### Test 2: Přidej položku s lokací
1. Tab "📦 Položky"
2. "+ Nová položka"
3. Vyplň:
   - Název: `Cement Portland`
   - Skladová lokace: `A-1-B` ← Vyber z dropdownu
   - Množství: `100`, Jednotka: `pytel`
   - Cena: `150`
   - Šarže: `LOT-2024-001`
   - Expirace: `2026-12-31`
4. Uložit

### Test 3: Výdej na zakázku
1. Klikni **oranžovou šipku 📤** u položky
2. Typ: **Výdej**
3. Množství: `30`
4. **Zakázka: Vyber nějakou existující** (povinné!)
5. "Provést"

→ Položka teď má 70 pytlů, v tab "Pohyby" vidíš záznam

### Test 4: Inventura
1. Tab "✅ Inventura"
2. "📋 Spustit inventuru"
3. Zadej napočítané množství (např. `65`)
4. "✅ Dokončit inventuru"

→ Stav se automaticky upraví na 65

---

## 🐛 TROUBLESHOOTING

### ❌ "ModuleNotFoundError: No module named 'warehouse_extended'"

**Problém:** Soubor `warehouse_extended.py` chybí

**Řešení:**
```bash
cd ~/Desktop/green-david-WORK
ls -la warehouse_extended.py
```
Pokud chybí, zkontroluj, že jsi rozbalil správný ZIP.

### ❌ Nevidím "Warehouse Extended Routes loaded"

**Problém:** main.py nemá warehouse kód

**Řešení:**
```bash
# Zkontroluj velikost main.py
wc -l main.py
```
Mělo by být **přes 4200 řádků**. Pokud má méně, warehouse kód tam není.

```bash
# Zkontroluj konec souboru
tail -5 main.py
```
Měl bys vidět:
```python
print("✅ Warehouse Extended Routes loaded")
```

### ❌ Rozhozená grafika (modré pozadí)

**Problém:** CSS se nenačítá

**Řešení:**
1. Zastav server (CTRL+C)
2. Vymaž cache prohlížeče: CMD+SHIFT+R (Mac) nebo CTRL+SHIFT+R
3. Spusť znovu: `python3 main.py`
4. Obnovit stránku v prohlížeči

---

## 📦 CO JE V BALÍČKU

```
green-david-WORK/
├── main.py                        ✅ Rozšířený o warehouse routes
├── warehouse_extended.py          ✅ NOVÝ - Backend warehouse API
├── warehouse.html                 ✅ Nové UI s taby
├── static/warehouse/              ✅ NOVÉ - 5 JS modulů
│   ├── items.js
│   ├── movements.js
│   ├── locations.js
│   ├── reservations.js
│   └── inventory.js
├── app.db                         ✅ Tvá současná databáze
└── ... všechny tvé soubory ...    ✅ Beze změny
```

**Zálohy vytvořené automaticky:**
- `main.py.BACKUP_BEFORE_WAREHOUSE` - původní main.py
- `warehouse.html.BACKUP` - původní warehouse.html

---

## 💾 DATABÁZE

**První spuštění:**
- Automaticky se aplikují warehouse migrace
- Vytvoří se nové tabulky (warehouse_locations, warehouse_movements, atd.)
- **Tvá současná data zůstávají BEZ ZMĚNY!**

**Záloha:**
Aplikace automaticky zálohovala tvou databázi:
```
app.db.backup_extended_greendavid
```

---

## 🎯 DŮLEŽITÉ

### ✅ Co FUNGUJE:
- Všechny tvé současné funkce (zakázky, zaměstnanci, atd.)
- Nový rozšířený sklad s 7 hlavními funkcemi
- Všechny CSS a JS soubory

### ✅ Co bylo PŘIDÁNO:
- `warehouse_extended.py` - Backend API
- `static/warehouse/*.js` - 5 nových modulů
- Nový `warehouse.html` - UI s taby
- Routes v `main.py` - API endpointy

### ✅ Co zůstalo BEZ ZMĚNY:
- Tvá databáze (jen nové tabulky)
- Všechny ostatní soubory
- Přihlašovací údaje
- Veškerá tvá data

---

## 🔄 ROLLBACK (pokud chceš zpět)

Pokud chceš vrátit změny:

```bash
cd ~/Desktop/green-david-WORK

# Vrať původní main.py
cp main.py.BACKUP_BEFORE_WAREHOUSE main.py

# Vrať původní warehouse.html
cp warehouse.html.BACKUP warehouse.html

# Smaž warehouse soubory
rm warehouse_extended.py
rm -rf static/warehouse

# Spusť
python3 main.py
```

---

## ✨ HOTOVO!

Máš nyní **plně funkční Green David App** s nadčasovým rozšířením skladu!

**Veškeré funkce:**
- ✅ Zakázky, zaměstnanci, výkazy
- ✅ Kalendář, úkoly, dokumenty
- ✅ Školka, plánování
- ✅ **NOVÝ:** Profesionální správa skladu

**Užij si! 🚀**

---

## 📞 Podpora

Pokud něco nefunguje:
1. Zkontroluj výstup v terminálu
2. Otevři konzoli prohlížeče (F12)
3. Pošli mi screenshoty obou

