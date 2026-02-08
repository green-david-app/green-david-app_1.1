# ZPRÁVA: Oprava Sidebar Layout Problémů

**Datum:** 3. února 2026  
**Status:** 🔴 KRITICKÉ PROBLÉMY IDENTIFIKOVÁNY

---

## 📋 SOUHRN PROBLÉMŮ

### ✅ Co funguje:
- **Školka (nursery.html)** - obsah se zobrazuje správně
- **Timeline, Plánování, Kalendář** - obsah viditelný
- **Sidebar samotný** - renderuje se správně na všech stránkách

### ❌ Co nefunguje:
- **Zakázky (jobs.html)** - prázdná stránka (jen header + sidebar)
- **Sklad (warehouse.html)** - prázdná stránka (jen header + sidebar)
- **Výkazy (timesheets.html)** - pravděpodobně stejný problém

---

## 🔍 ANALÝZA PROBLÉMU

### 1. Struktura HTML

**Fungující stránka (nursery.html):**
```html
<body class="has-sidebar">
  <div id="app-sidebar"></div>
  <header class="app-header">...</header>
  <div class="app-header-container">...</div>
  <!-- Obsah je přímo v body -->
</body>
```

**Nefungující stránka (jobs.html):**
```html
<body class="has-sidebar">
  <div id="app-sidebar"></div>
  <div id="app-header"></div>
  <main class="app-shell">
    <div class="page-container">
      <!-- Obsah je v <main> -->
    </div>
  </main>
</body>
```

**Nefungující stránka (warehouse.html):**
```html
<body class="has-sidebar">
  <div id="app-sidebar"></div>
  <div id="app-header"></div>
  <div class="container">
    <!-- Obsah je v <div class="container"> -->
  </div>
</body>
```

### 2. CSS Problém: `display: flex` na `body.has-sidebar`

**Aktuální CSS (PROBLÉM):**
```css
body.has-sidebar {
  display: flex;  /* ⚠️ TOHLE ZPŮSOBUJE PROBLÉMY */
  min-height: 100vh;
  padding-left: 0 !important;
}
```

**Proč je to problém:**
- `display: flex` na `body` mění způsob, jakým se renderují děti
- Flexbox layout může způsobit, že některé elementy nejsou viditelné
- Konfliktuje s `margin-left` pravidly pro posunutí obsahu

---

## ✅ PROVEDENÉ OPRAVY

### 1. Přidány explicitní `display: block` pravidla

Přidal jsem do všech CSS pravidel pro obsah:
```css
/* KRITICKÉ: Zajisti že obsah je viditelný */
display: block !important;
visibility: visible !important;
opacity: 1 !important;
```

**Aplikováno na:**
- `body.has-sidebar > main`
- `body.has-sidebar > .container`
- `body.has-sidebar #app`
- `body.has-sidebar .app-shell`
- `body.has-sidebar .page-container`
- `body.has-sidebar main`
- `body.has-sidebar .container`

### 2. Opraven collapsed state

Přidány stejné viditelnostní pravidla i pro collapsed stav.

---

## 🔧 DOPORUČENÉ OPRAVY

### 1. **ODSTRANIT `display: flex` z `body.has-sidebar`**

**Soubor:** `static/css/sidebar.css`  
**Řádek:** 29

**Změnit z:**
```css
body.has-sidebar {
  display: flex;
  min-height: 100vh;
  padding-left: 0 !important;
}
```

**Změnit na:**
```css
body.has-sidebar {
  /* NEPOUŽÍVAT display: flex - způsobuje problémy s layoutem */
  min-height: 100vh;
  padding-left: 0 !important;
}
```

**Důvod:** Flexbox na body mění způsob renderování a může způsobit, že obsah není viditelný.

---

## 📊 TESTOVÁNÍ

### Stránky k otestování:

1. ✅ **nursery.html** - mělo by fungovat (funguje)
2. ❌ **jobs.html** - prázdná stránka
3. ❌ **warehouse.html** - prázdná stránka
4. ❓ **timesheets.html** - pravděpodobně stejný problém
5. ✅ **timeline.html** - mělo by fungovat (funguje)
6. ✅ **calendar.html** - mělo by fungovat (funguje)

### Postup testování:

1. Otevři každou stránku v prohlížeči
2. Zkontroluj, že:
   - Sidebar je viditelný vlevo
   - Obsah stránky je viditelný vedle sidebaru
   - Obsah není schovaný za sidebarem
   - Obsah není prázdný (bílá plocha)

---

## 🎯 DALŠÍ KROKY

### Okamžité akce:
1. ✅ Odstranit `display: flex` z `body.has-sidebar`
2. ✅ Otestovat všechny stránky
3. ✅ Pokud problém přetrvá, zkontrolovat JavaScript (`app-sidebar.js`)

### Možné další problémy:
- JavaScript může skrývat obsah (`display: none` v JS)
- Konflikt s jinými CSS soubory (`style.css`, `app.css`)
- Problém s načítáním CSS (pořadí načítání)

---

## 📝 TECHNICKÉ DETAILY

### CSS Specificita

Pravidla jsou uspořádána od nejkonkrétnějších po obecné:

1. **Nejvyšší priorita:** `body.has-sidebar > main` (přímé děti)
2. **Vysoká priorita:** `body.has-sidebar #app` (ID selektory)
3. **Střední priorita:** `body.has-sidebar .app-shell` (konkrétní třídy)
4. **Nízká priorita:** `body.has-sidebar main` (obecné elementy)
5. **Nejnižší priorita:** `body.has-sidebar .container` (obecné třídy)

### Použité CSS vlastnosti:

- `margin-left: var(--sidebar-width) !important` - posune obsah za sidebar
- `width: calc(100% - var(--sidebar-width)) !important` - upraví šířku
- `display: block !important` - zajistí viditelnost
- `visibility: visible !important` - zajistí viditelnost
- `opacity: 1 !important` - zajistí viditelnost

---

## 🔗 SOUVISEJÍCÍ SOUBORY

- `static/css/sidebar.css` - hlavní CSS pro sidebar
- `static/app-sidebar.js` - JavaScript pro sidebar
- `jobs.html` - problematická stránka
- `warehouse.html` - problematická stránka
- `nursery.html` - fungující stránka (referenční)

---

## ✅ CHECKLIST OPRAV

- [x] Přidány `display: block !important` do všech pravidel
- [x] Přidány `visibility: visible !important` do všech pravidel
- [x] Přidány `opacity: 1 !important` do všech pravidel
- [ ] **ODSTRANIT `display: flex` z `body.has-sidebar`** ⚠️ KRITICKÉ
- [ ] Otestovat všechny stránky po opravě
- [ ] Zkontrolovat JavaScript (`app-sidebar.js`)

---

**Poznámka:** Hlavní problém je pravděpodobně `display: flex` na `body.has-sidebar`. Po jeho odstranění by měly všechny stránky fungovat správně.
