# SIDEBAR FIX - Finální opravy

## ✅ Provedené změny

### 1. CSS - Přepracovaná pravidla (`static/css/sidebar.css`)

**Problém:** Duplikáty a překrývající se pravidla způsobovaly dvojité posunutí nebo žádné posunutí.

**Řešení:** Pravidla seřazena od nejkonkrétnějších po obecné:

1. **Přímé děti body** (`> main`, `> .container`) - nejvyšší priorita
2. **Elementy s ID** (`#app`, `#app-content`) - s `display: block` pro jistotu
3. **Konkrétní třídy** (`.app-shell`, `.page-container`, `.page-content`)
4. **Obecné main** (`main:not(.app-sidebar)`)
5. **Obecné container** (`.container:not(.app-sidebar)`)

**Výhody:**
- Žádné duplikáty
- Správná specificita
- Všechny stránky pokryty

### 2. Collapsed state

Přidána všechna pravidla i pro collapsed state, aby se správně aktualizovalo při collapse/expand.

### 3. JavaScript - Odstraněn padding

- ✅ Odstraněn `document.body.style.paddingLeft` z `render()`
- ✅ Odstraněn `document.body.style.paddingLeft` z `updateState()`
- ✅ CSS řeší vše přes `margin-left` na kontejnerech

### 4. Body padding

- ✅ Přidáno `padding-left: 0 !important` do `body.has-sidebar` pro jistotu

## 📋 Testovací checklist

### Stránky k otestování:
- [ ] **index.html** (Přehled) - `<main class="container">` + `<div id="app">`
  - [ ] Není dvojité posunutí
  - [ ] Obsah je správně posunutý za sidebar
  
- [ ] **jobs.html** (Zakázky) - `<main class="app-shell">`
  - [ ] Obsah se zobrazuje (není prázdný)
  - [ ] Obsah je správně posunutý za sidebar
  
- [ ] **timesheets.html** (Výkazy) - `<main class="app-shell">`
  - [ ] Obsah není za sidebarem
  
- [ ] **calendar.html** (Kalendář)
  - [ ] Obsah není za sidebarem
  
- [ ] **planning-daily.html** (Plánování)
  - [ ] Obsah není za sidebarem
  
- [ ] **timeline.html** (Timeline)
  - [ ] Obsah není za sidebarem

### Obecné kontroly:
- [ ] Sidebar je viditelný na všech stránkách
- [ ] Header je správně posunutý
- [ ] Bottom nav není viditelný na desktopu
- [ ] Collapse/expand funguje správně
- [ ] Žádné JS errory v konzoli

## 🔧 Změněné soubory

1. `static/css/sidebar.css` - přepracovaná CSS pravidla (odstraněny duplikáty)
2. `static/app-sidebar.js` - odstraněn padding z body (CSS to řeší)

## ⚠️ Poznámky

- CSS pravidla jsou seřazena od nejkonkrétnějších po obecné
- Používáme pouze `margin-left` na kontejnerech, NIKDY `padding-left` na body
- Pro `#app` přidáno `display: block` a `visibility: visible` pro jistotu
- Všechna pravidla mají `!important` pro přebití lokálních stylů
