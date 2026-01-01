# Moderní ikony - Progress

## ✅ Dokončeno

1. **Vytvořeny soubory:**
   - `/static/icons.css` - CSS pro SVG ikony
   - `/static/navigation.js` - Automatické active states

2. **Upraveny soubory:**
   - `index.html` - Dashboard action cards (SVG ikony) + bottom navigation
   - `calendar.html` - Bottom navigation ikony opraveny

## 🔄 V procesu

3. **Potřeba upravit další soubory:**
   - `jobs.html` - pokud má bottom navigation
   - `tasks.html` - pokud má bottom navigation  
   - `settings.html` - pokud má bottom navigation
   - `templates/timesheets.html` - bottom navigation
   - `employees.html` (v templates/) - bottom navigation

## 📋 Postup

Pro každý HTML soubor:
1. Najít bottom-nav
2. Upravit SVG ikony podle specifikace:
   - Zakázky: projects SVG
   - Více: 3 tečky vertikálně
   - Nastavení: settings SVG
3. Přidat před `</body>`:
   ```html
   <script src="/static/navigation.js"></script>
   <link rel="stylesheet" href="/static/icons.css">
   ```

## ✅ Ikony specifikace

- Domů: Home SVG ✅
- Zakázky: Projects SVG (folder s dokumenty) ✅
- Výkazy: Clock SVG ✅
- Kalendář: Calendar SVG ✅
- Přehledy: Bar chart SVG ✅
- Více: 3 tečky vertikálně (circle 12,5 circle 12,12 circle 12,19) ✅
- Nastavení: Settings SVG (kolečko s čárami) ✅

