# Changelog - iOS Minimalist Redesign

## Kompletní redesign aplikace

### Nový Design System
- **Dark Theme**: Černé pozadí (#000000) s iOS style
- **Barvy**: Šedé/antracitové pozadí (#1c1c1e, #2c2c2e, #3a3a3c) + mátově zelené akcenty (#4ade80)
- **Typografie**: Inter font, iOS velikosti (17px base, 34px h1)
- **Komponenty**: Minimalistické, čisté, iOS-inspired

### Přepsané Templates
✅ **layout.html** - Nový header s iOS style
✅ **login.html** - Přepracovaný login formulář
✅ **timesheets.html** - Výkazy hodin s novým designem
✅ **calendar.html** - Kalendář s iOS style
✅ **search.html** - Vyhledávání
✅ **archive.html** - Archiv zakázek

### CSS
✅ **style.css** - Kompletně nový CSS s iOS minimalist designem
✅ **static/icons.css** - Minimalistické SVG ikony

### React Komponenty (index.html)
✅ **Login** - Upraven pro nový design
🔄 **JobsList, Tabs, další komponenty** - Používají nový CSS, automaticky se přizpůsobí

### Backend
✅ **main.py** - Zkopírován z původní verze
✅ **wsgi.py** - Zkopírován
✅ **requirements.txt** - Zkopírován
✅ **Procfile** - Zkopírován

### Mobile Preview
✅ **mobile-preview-export.html** - Standalone preview nového designu

## Jak spustit

```bash
cd green-david-app-redesigned
pip install -r requirements.txt
python main.py
```

Aplikace poběží na `http://localhost:5000`

## Deployment

1. Push do Git repozitáře
2. Vytvořit nový Web Service na Render
3. Spojit s repozitářem
4. Render automaticky detekuje `Procfile`

## Poznámky

- Všechny templates používají nový CSS z `style.css`
- React komponenty v `index.html` automaticky dědí nový design
- Design je optimalizován pro mobilní zařízení
- Používá CSS variables pro snadnou úpravu barev

