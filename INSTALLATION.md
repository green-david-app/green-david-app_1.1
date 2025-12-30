# 📦 Green David v3.0 - Instalační návod

## ✅ CO JE V BALÍČKU

### Nové soubory:
- `style.css` - Kompletní CSS framework (tmavý iOS design)
- `index.html` - Dashboard (hlavní stránka)
- `jobs.html` - Zakázky (seznam, filtry, modal pro přidání)
- `timesheets.html` - Výkazy hodin (timeline, filtry, statistiky)
- `employees.html` - Zaměstnanci
- `calendar.html` - Kalendář
- `archive.html` - Archiv zakázek
- `logo.jpg` - Vaše logo
- `js/employees.js` - JS logika pro zaměstnance

### Zachované soubory z původní aplikace:
- `main.py` - Backend (BEZ ZMĚN!)
- `wsgi.py` - WSGI entry point
- Databáze `app.db` - BEZ ZMĚN!

## 🚀 JAK NAINSTALOVAT

### Varianta A: Úplná náhrada (doporučeno)

```bash
# 1. Zálohujte současnou aplikaci
cp -r /path/to/green-david-app /path/to/green-david-app.backup

# 2. Nahraďte HTML a CSS soubory
cp style.css /path/to/green-david-app/
cp index.html /path/to/green-david-app/
cp jobs.html /path/to/green-david-app/
cp timesheets.html /path/to/green-david-app/
cp employees.html /path/to/green-david-app/
cp calendar.html /path/to/green-david-app/
cp archive.html /path/to/green-david-app/
cp logo.jpg /path/to/green-david-app/
cp -r js/ /path/to/green-david-app/

# 3. Restart aplikace
# (na Render.com se restartuje automaticky po git push)
```

### Varianta B: Postupná migrace

1. Nejdřív nahraďte jen `style.css`
2. Otestujte jak vypadá stará aplikace s novým CSS
3. Postupně nahrazujte HTML stránky

## ⚙️ KONFIGURACE

### Logo:
Logo `logo.jpg` je už v balíčku. Pokud chcete jiné:
```bash
cp /cesta/k/vasemu/logu.jpg /path/to/green-david-app/logo.jpg
```

### Backend:
Žádné změny nejsou potřeba! Backend (`main.py`) zůstává stejný.

### API endpointy:
Všechny API endpointy zůstávají stejné:
- `/api/jobs`
- `/api/employees`
- `/api/timesheets`
- `/api/archive`
- atd.

## ✅ OVĚŘENÍ

Po instalaci zkontrolujte:

1. **Dashboard (`/`):**
   - ✅ Zobrazuje se správně
   - ✅ Statistiky nahoře fungují
   - ✅ Quick actions fungují
   - ✅ Bottom navigation funguje

2. **Zakázky (`/jobs`):**
   - ✅ Seznam se načítá
   - ✅ Filtry fungují
   - ✅ Modal pro novou zakázku funguje

3. **Výkazy (`/timesheets`):**
   - ✅ Timeline se zobrazuje
   - ✅ Filtry fungují
   - ✅ Statistiky se počítají

4. **Zaměstnanci (`/employees`):**
   - ✅ Seznam se načítá
   - ✅ Karty se zobrazují správně

## 🎨 DESIGN FEATURES

✅ Tmavý elegantní design
✅ Původní Green David barvy (antracit + mátová)
✅ Moderní SVG ikony (Feather Icons style)
✅ Bottom navigation (iOS style)
✅ Responzivní (mobile-first)
✅ Loading states
✅ Empty states
✅ Modals pro formuláře

## 🐛 TROUBLESHOOTING

### Logo se nezobrazuje:
- Zkontrolujte že `logo.jpg` je v root složce aplikace
- Zkontrolujte práva (chmod 644 logo.jpg)

### CSS se nenačítá:
- Vyčistěte cache prohlížeče (Ctrl+Shift+R)
- Zkontrolujte že `style.css` je v root složce

### API nefunguje:
- Backend zůstává stejný, zkontrolujte že `main.py` běží
- Zkontrolujte konzoli prohlížeče (F12) pro chyby

### Bottom navigation překrývá obsah:
- To je normální, obsah má `padding-bottom: 90px`
- Pokud to vadí, upravte v `style.css`: `body { padding-bottom: 90px; }`

## 📞 PODPORA

Pokud něco nefunguje:
1. Zkontrolujte konzoli v prohlížeči (F12)
2. Zkontrolujte logy aplikace
3. Porovnejte s backup verzí

## 🎉 HOTOVO!

Aplikace by měla fungovat stejně jako předtím, jen vypadat mnohem lépe! 🚀
