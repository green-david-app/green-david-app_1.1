# Dark Mode Color Scheme - green david app

## Hlavní barvy

### Pozadí
- **Hlavní pozadí stránky**: `#1a1a1a` (tmavé)
- **Pozadí karet/kontejnerů**: `#1f2428` (tmavě šedé)
- **Pozadí hover stavů**: `#2a2f35` (světlejší tmavé)

### Buňky kalendáře
- **Normální buňky dnů**: `#3d5a4a` (světle zelené/tyrkysové)
- **Hover buňky**: `#4a6a5a` (světlejší zelená)
- **Prázdné dny (z jiného měsíce)**: `#2d4a3a` (tmavší zelená, opacity 0.6)
- **Víkendové dny**: `#3d5a4a` (stejné jako normální)
- **Dnešní den**: `#4ade80` (světle zelená s border)

### Text
- **Hlavní text na tmavém pozadí**: `#ffffff` (bílý)
- **Sekundární text na tmavém pozadí**: `#a0a0a0` (světle šedá)
- **Text v buňkách (čísla dnů)**: `#0a0e11` (tmavý na světlých buňkách)
- **Text v dnešním dni**: `#0a0e11` (tmavý na světle zeleném pozadí)

### Akcentní barvy
- **Zelená akcentní**: `#4ade80` (světle zelená)
- **Zelená hover**: `#5aee90` (ještě světlejší)
- **Mint zelená**: `#3ea76a`
- **Mint světlá**: `#4bb878`
- **Mint tmavá**: `#2d8f55`

### Badges/Chips
- **Pozadí badge**: `#2d4a3a` (tmavě zelené)
- **Text v badge**: `#ffffff` (bílý)
- **Border badge**: `rgba(255,255,255,0.2)` (bílá s průhledností)

### Borders
- **Hlavní border**: `#353b41` (tmavě šedá)
- **Border buňek**: `rgba(255,255,255,0.2)` (bílá s průhledností)

### Header/Navigation
- **Pozadí headeru**: `rgba(26,26,26,0.9)` (tmavé s průhledností)
- **Text v headeru**: `#ffffff` (bílý)
- **Linky v headeru**: `#4ade80` (světle zelená)

### Formuláře/Dialogy
- **Pozadí dialogu**: `#1f2428` (tmavě šedé)
- **Text v dialogu**: `#e8eef2` (světle šedá)
- **Border dialogu**: `#353b41` (tmavě šedá)

## CSS Proměnné (doporučené)

```css
:root {
  /* Dark Mode Backgrounds */
  --bg-primary: #1a1a1a;
  --bg-secondary: #1f2428;
  --bg-card: #1f2428;
  --bg-card-hover: #2a2f35;
  --bg-elevated: #1f2428;
  --bg-tertiary: #2a2f35;
  
  /* Calendar Cells */
  --cal-cell-bg: #3d5a4a;
  --cal-cell-hover: #4a6a5a;
  --cal-cell-muted: #2d4a3a;
  --cal-cell-today: #4ade80;
  
  /* Text Colors */
  --text-primary: #ffffff;
  --text-secondary: #a0a0a0;
  --text-on-light: #0a0e11;
  --text-tertiary: #9ca8b3;
  
  /* Accent Colors */
  --accent-green: #4ade80;
  --accent-green-hover: #5aee90;
  --mint: #3ea76a;
  --mint-light: #4bb878;
  --mint-dark: #2d8f55;
  
  /* Borders */
  --border-primary: #353b41;
  --border-light: rgba(255,255,255,0.2);
  
  /* Badges */
  --badge-bg: #2d4a3a;
  --badge-text: #ffffff;
}
```

## Aplikace na celou aplikaci

### Obecné pravidlo:
- **Tmavé pozadí** (`#1a1a1a`) pro celou stránku
- **Světlé buňky/karty** (`#3d5a4a`) pro obsah
- **Tmavý text** (`#0a0e11`) na světlých prvcích
- **Světlý text** (`#ffffff`) na tmavých prvcích
- **Zelené akcenty** (`#4ade80`) pro interaktivní prvky

### Komponenty:
1. **Karty**: `background: #1f2428`, `color: #e8eef2`
2. **Tlačítka**: `background: #4ade80`, `color: #0a0e11`
3. **Inputy**: `background: #2a2f35`, `color: #ffffff`, `border: #353b41`
4. **Tabulky**: `background: #1f2428`, `color: #e8eef2`
5. **Navigace**: `background: rgba(26,26,26,0.9)`, `color: #ffffff`

## Poznámky

- Všechny barvy jsou navrženy pro dark mode
- Kontrast je optimalizován pro čitelnost
- Zelené akcenty jsou konzistentní s brandem aplikace
- Hover efekty používají světlejší odstíny

