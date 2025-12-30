# Green David App - iOS Minimalist Redesign

Kompletně přepracovaná aplikace s novým iOS minimalistickým designem.

## Nový Design

- **Dark Theme**: Černé pozadí (#000000) s iOS style
- **Barvy**: Šedé/antracitové pozadí + mátově zelené akcenty (#4ade80)
- **Typografie**: Inter font, iOS style velikosti
- **Komponenty**: Minimalistické, čisté, iOS-inspired

## Struktura

```
green-david-app-redesigned/
├── style.css              # Nový iOS minimalist CSS
├── static/
│   └── icons.css         # Minimalistické SVG ikony
├── index.html            # Hlavní React SPA
├── main.py               # Flask backend
├── wsgi.py               # WSGI entry point
├── requirements.txt      # Python závislosti
└── Procfile             # Render deployment
```

## Spuštění

```bash
pip install -r requirements.txt
python main.py
```

Aplikace poběží na `http://localhost:5000`

## Deployment na Render

1. Push do Git repozitáře
2. Vytvořit nový Web Service na Render
3. Spojit s repozitářem
4. Render automaticky detekuje `Procfile`

## Změny oproti původní verzi

- Kompletně nový CSS s iOS style
- Dark theme s černým pozadím
- Mátově zelené akcenty místo původních barev
- Minimalistické ikony
- Optimalizace pro mobilní zařízení

