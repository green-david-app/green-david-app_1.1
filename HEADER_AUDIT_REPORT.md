# HEADER AUDIT REPORT - Pre-Deploy
**Datum:** 2025-02-02

## AUDIT 1: CSS KONFLIKTY

### 1.1 Všechny .app-header styly

**VÝSLEDEK:** ✅/⚠️ **ČÁSTEČNĚ OK**

Nalezeno v:
- ✅ `static/css/mobile-header.css` - NOVÝ kompaktní header (s !important)
- ✅ `static/css/app.css` - NOVÝ header s !important (řádek 7195)
- ⚠️ `static/css/app.css` - **STARÉ styly stále existují** (řádky 6630-7177):
  - `.app-header-notifications`
  - `.app-header-subtitle`
  - `.app-header-title`
  - `.app-header-logo`
  - `.app-header-text`
  - `.app-header-left`
  - `.app-header-center`
  - `.app-header-tasks`
  - `.app-header-badge`
  - `.app-header-notification`
  - `.app-header-logout`
  - A další...

**PROBLÉM:** Staré CSS třídy mohou konfliktovat, ale protože nový header používá jiné třídy (`.header-btn`, `.header-left`, atd.), nemělo by to být problém. **DOPORUČENÍ:** Smazat staré `.app-header-*` styly z `app.css` pro čistotu.

### 1.2 Pořadí načítání CSS

**VÝSLEDEK:** ✅ **OK**

**layout_mobile_field.html:**
```
1. style.css
2. css/app.css          ← STARÉ styly
3. css/mobile_field.css
4. css/widgets.css
5. css/voice-input.css
6. css/mobile-header.css ← NOVÉ styly (POSLEDNÍ) ✅
7. icons.css
```

**layout_mobile_full.html:**
```
1. style.css
2. css/app.css          ← STARÉ styly
3. css/mobile_full.css
4. css/widgets.css
5. css/voice-input.css
6. css/mobile-header.css ← NOVÉ styly (POSLEDNÍ) ✅
7. icons.css
```

**layout.html (desktop):**
```
1. style.css
2. css/app.css
3. icons.css
(NEMÁ mobile-header.css - OK, desktop používá app-header.js)
```

**ZÁVĚR:** ✅ `mobile-header.css` se načítá POSLEDNÍ, takže !important funguje správně.

### 1.3 !important použití

**VÝSLEDEK:** ✅ **OK**

- `mobile-header.css`: **49x** !important (dostatečné pokrytí)
- `app.css` pro header: **3x** !important (v novém headeru)

**ZÁVĚR:** ✅ Použití !important je správné a dostatečné.

---

## AUDIT 2: JAVASCRIPT KONFLIKTY

### 2.1 Manipulace s headerem v JS

**VÝSLEDEK:** ⚠️ **POTENCIÁLNÍ PROBLÉM**

Nalezeno:
- `static/js/components/header-broken.js` - starý kód (možná nepoužívaný?)
- `static/js/components/header-fixed.js` - starý kód (možná nepoužívaný?)
- `static/js/ai-operator-drawer.js` - hledá `.app-header-actions` (stará třída)
- `static/app-header.js` - **STÁLE EXISTUJE** a může přepisovat header!

**KRITICKÉ:** `app-header.js` je stále načtený v `templates/layout.html` (řádek 198). Pokud nějaká stránka používá `layout.html` místo mobile layouts, header bude přepsán!

### 2.2 app-header.js reference

**VÝSLEDEK:** ⚠️ **ČÁSTEČNĚ OK**

Nalezeno:
- ✅ `templates/trainings.html` - **VYPNUTO** (komentář)
- ⚠️ `templates/layout.html` - **STÁLE NAČTENÝ** (řádek 198)
- ⚠️ `index.html` - **STÁLE NAČTENÝ** (řádek 13)

**PROBLÉM:** `layout.html` se používá pro desktop. Pokud mobile routes používají `layout.html`, header bude přepsán `app-header.js`.

**DOPORUČENÍ:** Zkontrolovat, které routes používají `layout.html` vs mobile layouts.

### 2.3 toggleHeaderMenu a toggleMobileMode

**VÝSLEDEK:** ⚠️ **DUPLICITY**

**toggleHeaderMenu:**
- ✅ `static/js/header.js` - hlavní definice (řádek 14)
- ⚠️ `templates/trainings.html` - duplicitní definice (řádek 1558)

**toggleMobileMode:**
- ✅ `static/js/header.js` - hlavní definice (řádek 87)
- ⚠️ `templates/trainings.html` - duplicitní definice (řádek 1579)

**PROBLÉM:** Duplicitní definice v `trainings.html`. Pokud se `header.js` načte před inline scriptem, inline script přepíše funkce. Pokud se načte po, inline script bude přepsán.

**DOPORUČENÍ:** Odstranit duplicitní definice z `trainings.html` - používat pouze `header.js`.

---

## AUDIT 3: HTML STRUKTURA

### 3.1 Header HTML

**VÝSLEDEK:** ✅ **OK** (s očekávanými rozdíly)

**layout_mobile_field.html:**
- ✅ Logo vlevo
- ✅ Center: `current-context` (dynamický podle zakázky)
- ✅ Right: mode-toggle (grid ikona), notifications, menu
- ✅ `data-current-mode="field"`

**layout_mobile_full.html:**
- ✅ Logo vlevo
- ✅ Center: `header-title` (statický "Green David")
- ✅ Right: mode-toggle (home ikona), notifications, menu
- ✅ `data-current-mode="full"`

**ZÁVĚR:** ✅ Rozdíly jsou ZÁMĚRNÉ (field má dynamický context, full má statický title).

### 3.2 Dropdown HTML

**VÝSLEDEK:** ✅ **OK**

Oba layouty mají:
- ✅ User info s avatarem
- ✅ Mode info
- ✅ Menu items (Upravit widgety, Synchronizace, Odhlásit)
- ✅ Overlay pro zavření

**ZÁVĚR:** ✅ Dropdown je konzistentní.

### 3.3 Konzistence

**VÝSLEDEK:** ✅ **OK**

Oba layouty mají:
- ✅ Stejný header HTML strukturu
- ✅ Stejný dropdown HTML
- ✅ Stejné CSS importy (pořadí)
- ✅ Stejné JS importy (`header.js`)

**ZÁVĚR:** ✅ Konzistence je zachována.

---

## AUDIT 4: TEMPLATE DĚDIČNOST

### 4.1 Extends

**VÝSLEDEK:** ✅ **OK**

- `templates/mobile/dashboard.html` → `extends "layouts/layout_mobile_" + mobile_mode + ".html"`
- Mobile routes používají mobile layouts ✅

### 4.2 Hlavní stránka

**VÝSLEDEK:** ⚠️ **POUŽÍVÁ STARÝ HEADER**

- Route `/` renderuje `index.html` (řádek 2512: `send_from_directory(".", "index.html")`)
- `index.html` načítá `app-header.js` (řádek 13)
- `index.html` má `<div id="app-header"></div>` (řádek 34)
- **PROBLÉM:** Hlavní stránka používá starý header z `app-header.js`, ne nový kompaktní header

**DOPORUČENÍ:** 
- Pokud je `index.html` pouze pro desktop → OK
- Pokud se očekává, že bude fungovat i na mobilu → přidat nový header nebo přesměrovat na `/mobile/dashboard`

---

## AUDIT 5: ENDPOINT PRO MODE TOGGLE

### 5.1 Endpoint existence

**VÝSLEDEK:** ✅ **OK**

- Endpoint: `/api/user/settings`
- Metody: GET, PATCH ✅
- Řádek: 3222

### 5.2 Endpoint implementace

**VÝSLEDEK:** ✅ **OK**

Endpoint:
- ✅ Přijímá PATCH
- ✅ Bere `mobile_mode` z JSON body
- ✅ Validuje hodnoty (`field`, `full`, `auto`)
- ✅ Ukládá do DB (`user_settings` tabulka)
- ✅ Vrací JSON response

**ZÁVĚR:** ✅ Endpoint je správně implementován.

---

## AUDIT 6: SOUHRNNÝ REPORT

```
HEADER AUDIT REPORT
====================

CSS:
- [OK] mobile-header.css se načítá POSLEDNÍ
- [⚠️] Staré .app-header-* styly stále existují v app.css (nekonfliktují, ale zbytečné)
- [OK] !important je použitý správně (49x v mobile-header.css)

JavaScript:
- [⚠️] app-header.js je STÁLE v layout.html (může přepisovat header na desktopu)
- [⚠️] toggleHeaderMenu() je definována 2x (header.js + trainings.html inline)
- [⚠️] toggleMobileMode() je definována 2x (header.js + trainings.html inline)
- [OK] Funkce jsou načtené ve všech mobile layoutech

HTML:
- [OK] Header je konzistentní v obou layoutech (rozdíly jsou záměrné)
- [OK] Dropdown existuje v obou layoutech
- [OK] Header má: logo, title, mode-toggle, notif, menu

Template dědičnost:
- [OK] Mobile routes používají mobile layouts
- [⚠️] Hlavní stránka (/) používá index.html s app-header.js (starý header)

Mode toggle:
- [OK] /api/user/settings endpoint existuje a funguje

ZÁVĚR: [NEEDS FIXES]
```

---

## NALEZENÉ PROBLÉMY A DOPORUČENÍ

### 🔴 KRITICKÉ (opravit před deployem):

1. **Duplicitní JavaScript v trainings.html**
   - **Problém:** `toggleHeaderMenu()` a `toggleMobileMode()` jsou definované jak v `header.js`, tak inline v `trainings.html`
   - **Riziko:** Konflikt, funkce mohou být přepsány
   - **Oprava:** Odstranit inline definice z `trainings.html` (řádky 1558-1595)

2. **app-header.js v layout.html**
   - **Problém:** Pokud nějaká stránka používá `layout.html`, header bude přepsán
   - **Riziko:** Nový header se nezobrazí na desktopu
   - **Oprava:** Buď:
     - A) Odstranit `app-header.js` z `layout.html` a použít nový header i na desktopu
     - B) Nebo zajistit, že mobile routes NIKDY nepoužívají `layout.html`

### 🟡 VAROVÁNÍ (doporučeno opravit):

3. **Staré CSS třídy v app.css**
   - **Problém:** Staré `.app-header-*` styly stále existují (řádky 6630-7177)
   - **Riziko:** Zbytečné CSS, může způsobit zmatky
   - **Oprava:** Smazat staré styly z `app.css` (nekonfliktují, ale zbytečné)

4. **Hlavní stránka používá starý header**
   - **Problém:** `index.html` používá `app-header.js` (starý header)
   - **Riziko:** Na mobilu se nezobrazí nový kompaktní header
   - **Oprava:** Buď:
     - A) Přidat nový header do `index.html` a odstranit `app-header.js`
     - B) Nebo přesměrovat `/` na `/mobile/dashboard` na mobilních zařízeních
     - C) Nebo ponechat jako je (pokud je index.html pouze pro desktop)

### ✅ OK (žádné změny):

- CSS pořadí načítání
- !important použití
- HTML struktura headeru
- Dropdown struktura
- Endpoint pro mode toggle
- Mobile layouts konzistence

---

## DOPORUČENÉ OPRAVY PŘED DEPLOYEM

### 1. Odstranit duplicitní JS z trainings.html

```bash
# Odstranit řádky 1558-1595 (inline toggleHeaderMenu a toggleMobileMode)
# Funkce už jsou v header.js, který se načítá
```

### 2. Zkontrolovat hlavní stránku

```bash
# Zkontrolovat def index() v main.py
# Pokud používá layout.html, buď:
# A) Změnit na mobile layout
# B) Nebo přidat nový header i do layout.html
```

### 3. (Volitelné) Vyčistit staré CSS

```bash
# Smazat staré .app-header-* styly z app.css (řádky 6630-7177)
# Nejsou kritické, ale zbytečné
```

---

## FINÁLNÍ HODNOCENÍ

**STATUS:** ⚠️ **NEEDS FIXES**

**Kritické problémy:** 2
**Varování:** 2
**OK:** 6

**DOPORUČENÍ:** Opravit kritické problémy před deployem, zejména duplicitní JavaScript a zkontrolovat hlavní stránku.
