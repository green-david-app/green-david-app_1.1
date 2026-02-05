# Testing Checklist - Sidebar Implementation

## ✅ Co bylo implementováno

### Nové soubory:
- `static/app-sidebar.js` - Sidebar komponenta
- `static/css/sidebar.css` - Sidebar styly
- `static/css/responsive.css` - Responsive CSS

### Upravené soubory:
- `static/app-header.js` - Sidebar toggle
- `static/bottom-nav.js` - Desktop check
- `main.py` - Routing pro FULL mode
- `static/css/app.css` - Toggle button styles
- `index.html` - Sidebar integrace

---

## 🧪 Testování

### Desktop (>1024px):
1. Otevři `/` → `index.html`
2. ✅ Sidebar viditelný vlevo (240px)
3. ✅ Header se posune doprava
4. ✅ Obsah se posune doprava
5. ✅ Klikni na toggle (×) → sidebar se zkolabuje na 64px
6. ✅ Klikni znovu → sidebar se rozbalí
7. ✅ Aktivní stránka zvýrazněná (zelená)
8. ✅ Bottom nav SKRYTÝ
9. ✅ Klikni na položku v sidebaru → navigace funguje

### Tablet (768-1024px):
1. Změň šířku okna na 768-1024px
2. ✅ Sidebar zkolabovaný (64px, jen ikony)
3. ✅ Hover na sidebar → expanduje na 240px
4. ✅ Bottom nav SKRYTÝ

### Mobil (<768px) FULL mode:
1. Otevři na mobilu nebo Chrome DevTools → Toggle Device
2. ✅ Sidebar skrytý (transform: translateX(-100%))
3. ✅ Klikni na hamburger v headeru → sidebar se otevře jako overlay
4. ✅ Klikni mimo sidebar nebo na overlay → sidebar se zavře
5. ✅ Bottom nav viditelný
6. ✅ Obsah responsivní (tabulky scroll, karty 1 sloupec)
7. ✅ Mode toggle "Komplet → Terén" viditelný v headeru

### Mobil FIELD mode:
1. Přepni do FIELD mode (pomocí toggle)
2. ✅ Přesměruje na `/mobile/today` (Jinja template)
3. ✅ Beze změny (starý mobile layout)

---

## 🐛 Možné problémy

### Sidebar se nezobrazuje:
- Zkontroluj že `index.html` má `<body class="has-sidebar">`
- Zkontroluj že `<div id="app-sidebar"></div>` je před `<header>`
- Zkontroluj že `app-sidebar.js` je načtený

### Header se neposune:
- Zkontroluj že `sidebar.css` je načtený
- Zkontroluj že `has-sidebar` třída je na `<body>`

### Bottom nav se nezobrazí na mobilu:
- Zkontroluj že `bottom-nav.js` má správnou logiku pro desktop check
- Zkontroluj že na mobilu není `has-sidebar` třída (nebo že je správně detekován mobil)

### Routing nefunguje:
- Zkontroluj že `main.py` má správnou logiku pro `mobile_mode`
- Zkontroluj že cookie `mobile_mode` je nastavená správně

---

## 📝 Poznámky

- Sidebar si pamatuje stav (collapsed/open) v localStorage
- Routing: FULL mode zobrazuje desktop stránky s responsive CSS
- Bottom nav se automaticky skryje na desktopu když je sidebar
- Header se přizpůsobí: desktop s sidebarem = hamburger + page title, mobil = plný header

---

## ✅ Pokud vše funguje

Pokračuj přidáním sidebaru do dalších prioritních stránek:
1. `jobs.html`
2. `warehouse.html`
3. `finance.html`
4. `tasks.html`
5. `team.html` / `employees.html`
6. `timesheets.html`
7. `calendar.html`
8. `reports.html`
9. `settings.html`
