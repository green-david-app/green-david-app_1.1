# 🔧 POKROČILÉ NÁSTROJE PRO NURSERY

## Přehled nástrojů

V menu "🔧 Nástroje" najdeš 4 pokročilé funkce pro efektivnější správu školky:

### 1. 📊 Export do Excel

**Co dělá:**
- Exportuje všechny rostliny do Excel souboru
- Generuje reporty a statistiky
- Umožňuje offline práci s daty

**Jak použít:**
1. Klikni "🔧 Nástroje" → "📊 Export do Excel"
2. Soubor se stáhne automaticky
3. Otevři v Excelu/LibreOffice

**Co obsahuje:**
- List "Rostliny" - všechny rostliny s detaily
- List "Statistiky" - přehledy podle fází
- List "Hodnota" - finanční přehledy
- List "Zalévání" - plán a historie

**Implementace (TODO):**
```javascript
async function exportToExcel() {
    const response = await fetch('/api/nursery/export/excel');
    const blob = await response.blob();
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `nursery_${new Date().toISOString().split('T')[0]}.xlsx`;
    a.click();
}
```

---

### 2. ✏️ Hromadná úprava

**Co dělá:**
- Upraví více rostlin najednou
- Ušetří čas při velkých změnách
- Zachová historii změn

**Možnosti:**
- **Změna lokace** - Přesuň celou skupinu rostlin
- **Změna fáze** - Postupuj skupinu do další fáze
- **Změna ceny** - Aktualizuj ceny podle %
- **Přidání poznámky** - Přidej poznámku ke skupině

**Jak použít:**
1. Filtruj rostliny (např. jen sazenice)
2. Klikni "🔧 Nástroje" → "✏️ Hromadná úprava"
3. Vyber, co chceš změnit
4. Aplikuj změny

**Příklad použití:**
```
Scénář: Přesun všech sazenic z Skleník 1 do Skleník 2

1. Filtr → Sazenice
2. Hromadná úprava → Změna lokace
3. Nová lokace: "Skleník 2"
4. Aplikovat (změní se všechny sazenice)
```

**Implementace (TODO):**
```javascript
async function batchUpdateLocation(newLocation) {
    const selectedPlants = getSelectedPlants(); // Podle filtru
    
    const response = await fetch('/api/nursery/batch-update', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({
            plant_ids: selectedPlants.map(p => p.id),
            updates: { location: newLocation }
        })
    });
    
    if (response.ok) {
        loadData(); // Refresh
    }
}
```

---

### 3. 📈 Pokročilé statistiky

**Co dělá:**
- Zobrazí detailní grafy a analýzy
- Sleduje trendy růstu a prodeje
- Pomáhá s plánováním

**Grafy a reporty:**

#### 📊 Dashboard
- **Růst v čase** - Kolik rostlin přibylo každý měsíc
- **Prodeje** - Trend prodejů podle měsíců
- **Ziskovost** - Marže podle druhů rostlin
- **Top 10** - Nejprodávanější druhy

#### 💰 Finanční analýza
- **Hodnota skladu** - Rozdělení podle fází
- **ROI** - Návratnost investice podle druhů
- **Zisk/Ztráta** - Porovnání nákupní vs prodejní ceny
- **Cashflow** - Předpokládané příjmy z prodeje

#### 🌱 Produkční analýza
- **Doba pěstování** - Průměrná doba od semínka po prodej
- **Úspěšnost** - % rostlin, které dospějí k prodeji
- **Kapacita** - Využití prostoru ve sklenících
- **Sezónnost** - Kdy se daří nejvíc druhům

**Jak použít:**
1. Klikni "🔧 Nástroje" → "📈 Pokročilé statistiky"
2. Otevře se dashboard s grafy
3. Filtruj podle období (týden/měsíc/rok)
4. Export grafů do PDF

**Implementace (TODO):**
Použij knihovnu Chart.js nebo Recharts:
```javascript
async function showStatistics() {
    const stats = await fetch('/api/nursery/statistics').then(r => r.json());
    
    // Vytvoř graf
    new Chart(ctx, {
        type: 'line',
        data: {
            labels: stats.months,
            datasets: [{
                label: 'Růst počtu rostlin',
                data: stats.growth
            }]
        }
    });
}
```

---

### 4. 🏷️ Tisk etiket

**Co dělá:**
- Vytiskne štítky pro rostliny
- Obsahuje QR kód pro rychlou identifikaci
- Standardizovaný formát pro školku

**Formát etikety:**
```
┌─────────────────────────┐
│  Echinacea purpurea    │
│  'Magnus'               │
│                         │
│  [QR CODE]              │
│                         │
│  Lokace: Skleník 1-A3   │
│  Cena: 89 Kč            │
│  Množství: 50 ks        │
└─────────────────────────┘
```

**Možnosti tisku:**
- **Jedna rostlina** - Tiskni štítek pro detail
- **Výběr** - Tiskni podle filtru (např. všechny prodejní)
- **Všechny** - Tiskni všechny rostliny

**QR kód obsahuje:**
- ID rostliny
- URL: `https://app.greendavid.cz/nursery/plant/123`
- Rychlý přístup přes mobil

**Jak použít:**
1. Filtruj rostliny (např. prodejní)
2. Klikni "🔧 Nástroje" → "🏷️ Tisk etiket"
3. Vyber formát štítku (A4, štítky 70x35mm)
4. Náhled před tiskem
5. Tiskni

**Implementace (TODO):**
```javascript
async function printLabels() {
    const plants = getFilteredPlants();
    
    // Generuj PDF s etiketami
    const response = await fetch('/api/nursery/print-labels', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({
            plant_ids: plants.map(p => p.id),
            format: 'A4_70x35'
        })
    });
    
    const blob = await response.blob();
    const url = window.URL.createObjectURL(blob);
    window.open(url); // Otevře PDF
}
```

**Backend (Python):**
```python
from reportlab.pdfgen import canvas
import qrcode

@app.route('/api/nursery/print-labels', methods=['POST'])
def print_labels():
    data = request.json
    plant_ids = data['plant_ids']
    
    # Načti rostliny
    plants = db.execute(
        "SELECT * FROM nursery_plants WHERE id IN (?)",
        plant_ids
    ).fetchall()
    
    # Vytvoř PDF
    pdf = canvas.Canvas("labels.pdf")
    
    for plant in plants:
        # Generuj QR kód
        qr = qrcode.make(f"https://app.greendavid.cz/nursery/plant/{plant['id']}")
        
        # Vykreslí etiketu
        pdf.drawString(50, 750, plant['species'])
        pdf.drawImage(qr_img, 50, 650, 100, 100)
        # ... další pole
        
        pdf.showPage()
    
    pdf.save()
    return send_file("labels.pdf")
```

---

## Roadmap implementace

### Fáze 1: Export (2-3 hodiny)
1. ✅ Základní UI menu
2. ⏳ Backend endpoint pro export
3. ⏳ Generování Excel souboru
4. ⏳ Formátování listů

### Fáze 2: Hromadné úpravy (3-4 hodiny)
1. ⏳ UI pro výběr rostlin
2. ⏳ Modální dialog s opcemi
3. ⏳ Backend endpoint pro batch update
4. ⏳ Validace a error handling

### Fáze 3: Statistiky (1 den)
1. ⏳ Backend endpoint pro statistická data
2. ⏳ Integrace Chart.js
3. ⏳ Dashboard s grafy
4. ⏳ Export grafů do PDF

### Fáze 4: Etikety (4-6 hodin)
1. ⏳ QR kód generování
2. ⏳ PDF layout s ReportLab
3. ⏳ Preview před tiskem
4. ⏳ Různé formáty etiket

---

## Tipy pro implementaci

### Export do Excel
- Použij knihovnu `openpyxl` (Python) nebo `xlsx` (JavaScript)
- Vytvoř template Excel soubor s formátováním
- Použij styling pro přehlednost

### Hromadné úpravy
- Vždy zobraz preview před aplikací
- Umožni undo funkci
- Loguj všechny změny do historie

### Statistiky
- Cachuj výpočty pro rychlost
- Použij indexy v databázi
- Generuj grafy asynchronně

### Etikety
- Testuj tisk na různých tiskárnách
- Nabídni různé velikosti etiket
- Umožni customizaci layoutu

---

## Časté dotazy

**Q: Lze exportovat jen vybrané rostliny?**
A: Ano, export respektuje aktuální filtry a vyhledávání.

**Q: Můžu hromadně upravit ceny?**
A: Ano, hromadná úprava podporuje % změnu cen (např. +10%).

**Q: Jsou statistiky v reálném čase?**
A: Ano, statistiky se počítají z aktuálních dat v databázi.

**Q: Jak velké etikety mohu tisknout?**
A: Podporujeme standardní formáty: 70x35mm, 50x25mm, A4 grid.

---

**Tyto nástroje výrazně zrychlí tvou práci se školkou! 🚀**
