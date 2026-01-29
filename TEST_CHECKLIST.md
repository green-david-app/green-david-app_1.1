# ✅ TESTOVACÍ CHECKLIST - Green David Warehouse Extended

## 🎯 PŘED STARTEM

- [ ] Python3 nainstalován
- [ ] Flask nainstalován (nebo se nainstaluje automaticky)
- [ ] Všechny soubory rozbalené ve stejné složce

---

## 🚀 SPUŠTĚNÍ

### Mac / Linux:
```bash
./start_local.sh
```

### Windows:
```cmd
start_local.bat
```

### Nebo manuálně:
```bash
python3 main.py
```

---

## 🔐 PŘIHLÁŠENÍ

1. Otevři prohlížeč: **http://127.0.0.1:5000**
2. Přihlaš se:
   - Email: `admin@greendavid.local`
   - Heslo: `admin123`

---

## ✅ TEST 1: Základní funkčnost

### Otevři Sklad:
- [ ] V menu klikni na "Sklad" nebo jdi na `/warehouse.html`
- [ ] Vidíš statistiky (0 hodnota, 0 položek atd.)
- [ ] Vidíš 5 tabů: 📦 Položky, 📍 Lokace, 📋 Pohyby, 🔒 Rezervace, ✅ Inventura

---

## ✅ TEST 2: Skladové lokace

1. **Přepni na tab "📍 Lokace"**
   - [ ] Vidíš prázdný seznam

2. **Vytvoř první lokaci:**
   - [ ] Klikni "+ Nová lokace"
   - [ ] Vyplň:
     - Kód: `A-1-B`
     - Název: `Sklad A, Regál 1, Police B`
     - Popis: `Testovací lokace`
   - [ ] Klikni "Uložit"
   - [ ] Lokace se objeví v seznamu

3. **Vytvoř druhou lokaci:**
   - [ ] Kód: `A-2-A`
   - [ ] Název: `Sklad A, Regál 2, Police A`
   - [ ] Uložit

**✅ Kontrola:**
- [ ] Vidíš 2 lokace v seznamu
- [ ] U každé je vidět kód, název, 0 položek

---

## ✅ TEST 3: Nová položka s lokací

1. **Přepni na tab "📦 Položky"**
   - [ ] Klikni "+ Nová položka"

2. **Vyplň formulář:**
   - Název: `Cement Portland`
   - SKU: `CEM-001`
   - Kategorie: `Stavební materiál`
   - **Skladová lokace: `A-1-B`** ← DŮLEŽITÉ
   - Množství: `100`
   - Jednotka: `pytel`
   - Cena: `150`
   - Minimální stav: `20`
   - Číslo šarže: `LOT-2024-001`
   - Expirace: `2026-12-31`

3. **Uložit**
   - [ ] Položka se objeví v seznamu
   - [ ] Vidíš badge lokace: 📍 A-1-B
   - [ ] Vidíš badge šarže: Šarže: LOT-2024-001

**✅ Kontrola statistik:**
- [ ] Celková hodnota: 15 000 Kč (100 × 150)
- [ ] Celkem položek: 1
- [ ] Nízký stav: 0
- [ ] Nedostupné: 0

---

## ✅ TEST 4: Vytvoř zakázku (pro test přiřazení)

1. **Otevři Zakázky** (`/jobs.html`)
2. **Vytvoř novou zakázku:**
   - Název: `Testovací stavba`
   - Kód: `TEST-001`
   - Stav: `Probíhá`
3. **Uložit**

---

## ✅ TEST 5: Výdej materiálu na zakázku

1. **Zpět do Skladu** (`/warehouse.html`)
2. **U položky "Cement Portland":**
   - [ ] Klikni na **oranžovou šipku 📤** (Vyskladnit)

3. **V modálním okně:**
   - [ ] Typ pohybu: **📤 Výdej** (už vybraný)
   - [ ] Množství: `30`
   - [ ] **Zakázka: Vyber "TEST-001 Testovací stavba"** ← POVINNÉ
   - [ ] Poznámka: `Výdej na testovací stavbu`
   - [ ] Klikni "Provést"

4. **Kontrola:**
   - [ ] Položka má teď množství: **70 pytel** (bylo 100)
   - [ ] V historii (vpravo dole) vidíš: "Výdej: Cement Portland (30 pytel)"

---

## ✅ TEST 6: Pohyby materiálu

1. **Přepni na tab "📋 Pohyby"**
   - [ ] Vidíš 1 záznam
   - [ ] Typ: 📤 Výdej
   - [ ] Položka: Cement Portland
   - [ ] Množství: +30 pytel (oranžové)
   - [ ] Zakázka: TEST-001 Testovací stavba
   - [ ] Šarže: LOT-2024-001
   - [ ] Čas a datum

---

## ✅ TEST 7: Vrácení materiálu

1. **Zpět na tab "📦 Položky"**
2. **U "Cement Portland":**
   - [ ] Klikni na detail (tužka)
   - [ ] V "Rychlé akce" najdi tlačítka
   - [ ] NEBO klikni oranžovou šipku a vyber typ "↩️ Vrácení"

3. **Formulář vrácení:**
   - [ ] Typ: **↩️ Vrácení**
   - [ ] Množství: `5`
   - [ ] Zakázka: `TEST-001 Testovací stavba`
   - [ ] Poznámka: `Nepoužité, vráceno ze stavby`
   - [ ] "Provést"

4. **Kontrola:**
   - [ ] Množství teď: **75 pytel** (70 + 5)
   - [ ] V Pohybech vidíš 2 záznamy (Výdej a Vrácení)

---

## ✅ TEST 8: Rezervace materiálu

1. **Přepni na tab "🔒 Rezervace"**
   - [ ] Klikni "+ Nová rezervace"

2. **Formulář:**
   - [ ] Položka: `Cement Portland`
   - [ ] Množství: `20`
   - [ ] Zakázka: `TEST-001 Testovací stavba`
   - [ ] Rezervace od: **dnes**
   - [ ] Rezervace do: **za týden**
   - [ ] Poznámka: `Rezervace pro dokončení`
   - [ ] "Rezervovat"

3. **Kontrola:**
   - [ ] Vidíš 1 aktivní rezervaci
   - [ ] Status: 🔵 Aktivní
   - [ ] Množství: 20 pytel
   - [ ] Zakázka: TEST-001

**✅ Kontrola statistik:**
- [ ] Rezervováno: 20 (v horní liště)

---

## ✅ TEST 9: Zrušení rezervace

1. **U rezervace:**
   - [ ] Klikni tlačítko "Zrušit" (červený X)
   - [ ] Potvrď

2. **Kontrola:**
   - [ ] Rezervace zmizela ze seznamu
   - [ ] Nebo má status "Zrušeno"

---

## ✅ TEST 10: Inventurní režim

1. **Přepni na tab "✅ Inventura"**
   - [ ] Klikni "📋 Spustit inventuru"
   - [ ] Potvrď (můžeš zadat poznámku)

2. **Detail inventury se otevře:**
   - [ ] Vidíš seznam položek
   - [ ] U každé:
     - Očekáváno: 75 pytel (současný stav)
     - Napočítáno: prázdné pole

3. **Napočítej položku:**
   - [ ] Do pole "Napočítáno" zadej: `70` (simulace nedostatku)
   - [ ] Pole se automaticky uloží
   - [ ] Vidíš rozdíl: **-5 pytel** (červeně)

4. **Dokončit inventuru:**
   - [ ] Klikni "✅ Dokončit inventuru"
   - [ ] Potvrď

5. **Kontrola:**
   - [ ] Inventura má status "Dokončeno"
   - [ ] V Pohybech vidíš nový záznam: "⚙️ Korekce -5 pytel"
   - [ ] Položka má teď množství: **70 pytel**

---

## ✅ TEST 11: Přejmenování položky

1. **Tab "📦 Položky"**
2. **U "Cement Portland":**
   - [ ] Klikni na detail
   - [ ] V "Rychlé akce" klikni "✏️ Přejmenovat"
   - [ ] Zadej nový název: `Cement Portland 42.5R`
   - [ ] Potvrď

3. **Kontrola:**
   - [ ] Název se změnil
   - [ ] Všechny pohyby stále ukazují na tuto položku

---

## ✅ TEST 12: Sloučení položek

1. **Vytvoř duplicitní položku:**
   - [ ] Název: `Cement portland` (malá písmena)
   - [ ] Lokace: `A-2-A`
   - [ ] Množství: `50`
   - [ ] Kategorie: `Stavební materiál`

2. **Sloučit:**
   - [ ] U nové položky klikni na detail
   - [ ] "🔀 Sloučit s jinou"
   - [ ] Vyber cílovou: `Cement Portland 42.5R`
   - [ ] Potvrď

3. **Kontrola:**
   - [ ] Cílová položka má teď: **120 pytel** (70 + 50)
   - [ ] Duplicitní položka zmizela
   - [ ] Všechny pohyby přesunuty

---

## ✅ TEST 13: Filtrování

1. **Tab "📦 Položky"**
2. **Zkus filtry:**
   - [ ] Hledání: zadej "cement" → najde položku
   - [ ] Kategorie: vyber "Stavební materiál" → zobrazí
   - [ ] Lokace: vyber "A-1-B" → zobrazí

---

## ✅ TEST 14: Export

1. **Klikni "Export"** (vpravo nahoře)
2. **Kontrola:**
   - [ ] Stáhne se CSV soubor
   - [ ] Otevři v Excelu/Google Sheets
   - [ ] Vidíš všechny položky s lokacemi, šaržemi, expirací

---

## 🎉 FINÁLNÍ KONTROLA

### Statistiky v horní liště:
- [ ] Celková hodnota: správná (součet všech položek × ceny)
- [ ] Celkem položek: správný počet
- [ ] Nízký stav: 0 (žádná položka pod minimem)
- [ ] Nedostupné: 0
- [ ] Expirující (30d): 0 (datum expirace je daleko)
- [ ] Rezervováno: 0 (rezervace byla zrušena)

### Taby fungují:
- [ ] ✅ Položky - seznam, detail, vytvoření, editace
- [ ] ✅ Lokace - CRUD operace
- [ ] ✅ Pohyby - historie všech operací
- [ ] ✅ Rezervace - vytvoření, zrušení
- [ ] ✅ Inventura - spuštění, napočítání, dokončení

### Přiřazení k zakázkám:
- [ ] ✅ Výdej vyžaduje zakázku
- [ ] ✅ Vrácení spojené se zakázkou
- [ ] ✅ Historie pohybů ukazuje zakázku

### Lokace:
- [ ] ✅ Položky mají lokace
- [ ] ✅ Přesun mezi lokacemi funguje

### Šarže & Expirace:
- [ ] ✅ Položka má číslo šarže
- [ ] ✅ Datum expirace se zobrazuje
- [ ] ✅ Badge upozornění funguje

---

## 🐛 Pokud něco nefunguje:

1. **Otevři konzoli prohlížeče (F12)**
   - Zkontroluj chyby v záložce "Console"
   - Napiš mi, jaké chyby vidíš

2. **Zkontroluj terminál**
   - Jsou tam chybové hlášky?
   - Napiš mi, co vidíš

3. **Restart**
   - Zastav server (CTRL+C)
   - Smaž `app.db`
   - Spusť znovu `./start_local.sh`

---

## 📊 POKRYTÍ FUNKCÍ

Otestované funkce:
- ✅ Skladové lokace (vytvoření, editace, mazání)
- ✅ Přiřazení k zakázkám (výdej, vrácení)
- ✅ Rezervace materiálu (vytvoření, zrušení)
- ✅ Expirační datumy & Šarže (tracking)
- ✅ Přejmenování položek
- ✅ Slučování položek
- ✅ Inventurní režim (spuštění, napočítání, dokončení, korekce)
- ✅ Statistiky a reporting
- ✅ Filtrování a vyhledávání
- ✅ Export do CSV

---

**Hotovo! Pokud prošly všechny testy ✅, aplikace je 100% funkční! 🎉**
