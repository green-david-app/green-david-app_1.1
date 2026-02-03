# 📱 Mobile UI - Funkční odkazy

## Base URL
Aplikace běží na: **`http://localhost:5000`** (lokální vývoj) nebo **`https://tvoje-domena.onrender.com`** (produkce)

## Přímé odkazy

### Demo stránka (index)
```
/mobile-demo.html
```
**Funkční link:** `http://localhost:5000/mobile-demo.html`

---

### FIELD Mode (Terénní režim)
```
/mobile/demo?mode=field
```
**Funkční link:** `http://localhost:5000/mobile/demo?mode=field`

**Nebo:**
```
/mobile/today
```
**Funkční link:** `http://localhost:5000/mobile/today`

---

### FULL Mode (Management režim)
```
/mobile/demo?mode=full
```
**Funkční link:** `http://localhost:5000/mobile/demo?mode=full`

**Nebo:**
```
/mobile/dashboard?mode=full
```
**Funkční link:** `http://localhost:5000/mobile/dashboard?mode=full`

---

### Widget Editor
```
/mobile/edit-dashboard
```
**Funkční link:** `http://localhost:5000/mobile/edit-dashboard`

---

## Jak použít

1. **Spusť aplikaci:**
   ```bash
   python main.py
   ```
   nebo
   ```bash
   flask run
   ```

2. **Otevři demo stránku:**
   - Lokálně: `http://localhost:5000/mobile-demo.html`
   - Nebo přímo: `http://localhost:5000/mobile/demo?mode=field`

3. **Pro produkci:**
   - Nahraď `localhost:5000` za svoji produkční URL

---

## Co uvidíš

### FIELD Mode obsahuje:
- ✅ Kompaktní header s aktuální zakázkou
- ✅ Widget: Aktuální zakázka
- ✅ Widget: Rychlý zápis práce
- ✅ Widget: Moje úkoly dnes
- ✅ Widget: Přidat foto
- ✅ Widget: Výdej materiálu
- ✅ Widget: Nahlásit problém
- ✅ Widget: Stav synchronizace
- ✅ Bottom nav s rychlými akcemi

### FULL Mode obsahuje:
- ✅ Header s brandingem
- ✅ Widget: Oznámení
- ✅ Widget: Rizikové zakázky
- ✅ Widget: Zpožděné zakázky
- ✅ Widget: Vytížení týmu
- ✅ Widget: Skladové výstrahy
- ✅ Widget: Čerpání rozpočtu
- ✅ Bottom nav s management sekcemi

---

## Poznámky

- Všechny routes vyžadují **autentizaci** (musíš být přihlášen)
- Widgety se automaticky filtrují podle **role** uživatele
- Módy se dají **přepínat** pomocí tlačítka v headeru
- Widget Editor umožňuje **drag & drop** pro přeskupení
