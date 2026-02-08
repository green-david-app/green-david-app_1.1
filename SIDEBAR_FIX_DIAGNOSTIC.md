# SIDEBAR FIX - Diagnostika a opravy

## 🔍 Identifikované problémy

1. **Obsah zasahuje za sidebar** - některé stránky nemají margin-left
2. **Zakázky stránka prázdná** - obsah se nezobrazuje
3. **Dvojité posunutí** - hlavní stránka se posouvá moc doprava

## ✅ Provedené opravy

### 1. CSS - Přepracované pravidla (`static/css/sidebar.css`)
- ✅ Odstraněn `padding-left` z `body.has-sidebar` (způsoboval dvojité posunutí)
- ✅ Přepracována pravidla od nejkonkrétnějších po obecné:
  1. Přímé děti body (`> main`, `> .container`)
  2. Elementy s ID (`#app`, `#app-content`)
  3. Elementy s třídou (`.container`, `.page-container`, `.app-shell`)
  4. Obecné main elementy
- ✅ Přidáno `display: block !important` a `visibility: visible !important` pro `#app` (oprava prázdné stránky)

### 2. JavaScript - Odstraněn padding (`static/app-sidebar.js`)
- ✅ Odstraněn `document.body.style.paddingLeft` z `render()` (CSS to řeší)
- ✅ Odstraněn `document.body.style.paddingLeft` z `updateState()` (CSS to řeší)
- ✅ Zachován pouze header positioning

## 📋 Testovací checklist

### Stránky k otestování:
- [ ] **index.html** (Přehled) - zkontroluj že není dvojité posunutí
- [ ] **jobs.html** (Zakázky) - zkontroluj že se obsah zobrazuje
- [ ] **timesheets.html** (Výkazy) - zkontroluj že obsah není za sidebarem
- [ ] **calendar.html** (Kalendář) - zkontroluj že obsah není za sidebarem
- [ ] **planning-daily.html** (Plánování) - zkontroluj že obsah není za sidebarem
- [ ] **timeline.html** (Timeline) - zkontroluj že obsah není za sidebarem

### Kontroly:
- [ ] Sidebar je viditelný na všech stránkách
- [ ] Obsah je posunutý za sidebar (není schovaný)
- [ ] Není dvojité posunutí (obsah není moc vpravo)
- [ ] Header je správně posunutý
- [ ] Bottom nav není viditelný na desktopu

## 🔧 Změněné soubory

1. `static/css/sidebar.css` - přepracovaná CSS pravidla
2. `static/app-sidebar.js` - odstraněn padding z body

## ⚠️ Poznámky

- CSS pravidla jsou seřazena od nejkonkrétnějších po obecné
- Používáme pouze `margin-left` na kontejnerech, NIKDY `padding-left` na body
- Pro `#app` přidáno `display: block` a `visibility: visible` pro jistotu
