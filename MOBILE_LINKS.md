# 📱 Funkční odkazy pro Mobile UI

## Base URL
Pokud aplikace běží lokálně: **`http://localhost:5000`**

Pokud běží na produkci: **`https://tvoje-domena.onrender.com`** (nebo jiná tvá URL)

---

## 🎯 Hlavní demo stránka (doporučeno)
```
/mobile-demo.html
```
**Funkční link:** `http://localhost:5000/mobile-demo.html`

Tato stránka obsahuje všechny odkazy a automaticky detekuje správnou URL.

---

## 📲 FIELD Mode (Terénní režim)

### Demo s ukázkovými daty:
```
/mobile/demo?mode=field
```
**Funkční link:** `http://localhost:5000/mobile/demo?mode=field`

### Today Screen:
```
/mobile/today
```
**Funkční link:** `http://localhost:5000/mobile/today`

---

## 💼 FULL Mode (Management režim)

### Demo s ukázkovými daty:
```
/mobile/demo?mode=full
```
**Funkční link:** `http://localhost:5000/mobile/demo?mode=full`

### Dashboard:
```
/mobile/dashboard?mode=full
```
**Funkční link:** `http://localhost:5000/mobile/dashboard?mode=full`

---

## ⚙️ Widget Editor (vyžaduje přihlášení)
```
/mobile/edit-dashboard
```
**Funkční link:** `http://localhost:5000/mobile/edit-dashboard`

---

## ✅ Co uvidíš

### FIELD Mode obsahuje:
- ✅ Kompaktní header s aktuální zakázkou
- ✅ Widget: Aktuální zakázka
- ✅ Widget: Rychlý zápis práce (30min, 1h, 2h, 4h, 8h)
- ✅ Widget: Moje úkoly dnes
- ✅ Widget: Přidat foto
- ✅ Widget: Výdej materiálu
- ✅ Widget: Nahlásit problém
- ✅ Widget: Stav synchronizace (offline/online)
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

## 🚀 Jak použít

1. **Spusť aplikaci** (pokud neběží):
   ```bash
   python main.py
   ```
   nebo
   ```bash
   flask run
   ```

2. **Otevři v prohlížeči:**
   - `http://localhost:5000/mobile-demo.html` ← **nejjednodušší způsob**
   - Nebo přímo některý z výše uvedených odkazů

3. **Pro mobilní zařízení:**
   - Otevři na telefonu/tabletu
   - Nebo použij DevTools v prohlížeči (F12 → Device Toolbar)

---

## 🔄 Přepínání módu

V headeru každé stránky je tlačítko pro přepnutí mezi FIELD ↔ FULL módy.

---

## ⚠️ Poznámka

- Demo routes (`/mobile/demo`) fungují **bez přihlášení** s ukázkovými daty
- Ostatní routes (`/mobile/today`, `/mobile/dashboard`) také fungují bez přihlášení s demo daty
- Widget Editor vyžaduje přihlášení (pro ukládání změn)
