# Sidebar Implementation Status

**Datum:** 2025-02-02

## ✅ KROK 1: Nové soubory vytvořeny

1. ✅ `static/app-sidebar.js` - Sidebar komponenta s navigací
2. ✅ `static/css/sidebar.css` - Sidebar styly + layout přizpůsobení
3. ✅ `static/css/responsive.css` - Globální responsive pravidla pro mobilní FULL mode

## ✅ KROK 2: Existující soubory upraveny

1. ✅ `static/app-header.js` - Přidán sidebar toggle, zjednodušený header pro desktop
2. ✅ `static/bottom-nav.js` - Skryje se na desktopu když je sidebar
3. ✅ `main.py` - Routing: FULL mode → desktop stránky
4. ✅ `static/css/app.css` - Přidány styly pro sidebar toggle button

## ✅ KROK 3: index.html upraven

1. ✅ Přidán `<link rel="stylesheet" href="/static/css/sidebar.css"/>`
2. ✅ Přidán `<link rel="stylesheet" href="/static/css/responsive.css"/>`
3. ✅ Přidán `<script src="/static/app-sidebar.js"></script>`
4. ✅ Přidán `<div id="app-sidebar"></div>` před header
5. ✅ Přidána třída `has-sidebar` na `<body>`

## 📋 KROK 4: Další prioritní stránky (TODO)

Potřebují stejné úpravy jako index.html:

1. ⏳ `jobs.html`
2. ⏳ `warehouse.html`
3. ⏳ `finance.html`
4. ⏳ `tasks.html`
5. ⏳ `team.html` / `employees.html`
6. ⏳ `timesheets.html`
7. ⏳ `calendar.html`
8. ⏳ `reports.html`
9. ⏳ `settings.html`

**Úpravy pro každou stránku:**
```html
<!-- V <head>: -->
<link rel="stylesheet" href="/static/css/sidebar.css"/>
<link rel="stylesheet" href="/static/css/responsive.css"/>

<!-- V <body>: -->
<body class="has-sidebar">
  <div id="app-sidebar"></div>
  
  <!-- Před </body>: -->
  <script src="/static/app-sidebar.js"></script>
```

## 🧪 Testování

### Desktop (>1024px):
- [ ] Sidebar viditelný vlevo (240px)
- [ ] Header se posune doprava
- [ ] Obsah se posune doprava
- [ ] Sidebar collapse/expand funguje
- [ ] Aktivní stránka zvýrazněná
- [ ] Bottom nav SKRYTÝ

### Tablet (768-1024px):
- [ ] Sidebar zkolabovaný (64px, jen ikony)
- [ ] Expand on hover funguje

### Mobil (<768px) FULL mode:
- [ ] Sidebar jako overlay z hamburgeru
- [ ] Bottom nav viditelný
- [ ] Obsah responsivní (tabulky scroll, karty 1 sloupec)
- [ ] Mode toggle "Komplet → Terén" viditelný

### Mobil FIELD mode:
- [ ] Beze změny (Jinja šablony jako dříve)

## 📝 Poznámky

- Sidebar si pamatuje stav (collapsed/open) v localStorage
- Routing v main.py: FULL mode zobrazuje desktop stránky s responsive CSS
- Bottom nav se automaticky skryje na desktopu když je sidebar
- Header se přizpůsobí: desktop s sidebarem = hamburger + page title, mobil = plný header
