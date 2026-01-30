# 🌸 NURSERY MODULE - Trvalkové školka

## Přehled

Modul pro správu trvalkové školky s kompletní funkcionalitou pro sledování rostlin, jejich růstových fází, lokací, cen a zálévání.

## Funkce

### ✅ Hotové funkce

1. **Správa rostlin**
   - Přidání nové rostliny
   - Úprava existující rostliny
   - Mazání rostliny
   - Detail rostliny

2. **Sledování růstových fází**
   - Semínko
   - Sazenice
   - Prodejní

3. **Evidence zálévání**
   - Plán zalévání
   - Zaznamenání zalití
   - Připomínky k zalití

4. **Statistiky a přehledy**
   - Celkový počet rostlin
   - Rostliny připravené k prodeji
   - Rostliny v pěstování
   - Hodnota skladu

5. **Vyhledávání a filtry**
   - Vyhledávání podle názvu
   - Filtrování podle růstové fáze
   - Seřazení podle různých kritérií

## Databázová struktura

### Tabulka: nursery_plants

```sql
CREATE TABLE nursery_plants (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    species TEXT NOT NULL,              -- Druh (např. Echinacea purpurea)
    variety TEXT,                       -- Odrůda (např. Magnus)
    quantity INTEGER DEFAULT 0,         -- Počet kusů
    stage TEXT DEFAULT 'semínko',       -- Fáze: semínko, sazenice, prodejní
    location TEXT,                      -- Lokace ve skleníku/školce
    planted_date DATE,                  -- Datum zasazení
    purchase_price REAL,                -- Nákupní cena za kus
    selling_price REAL,                 -- Prodejní cena za kus
    notes TEXT,                         -- Poznámky
    status TEXT DEFAULT 'active',       -- Status: active, sold, dead
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### Tabulka: nursery_watering_schedule

```sql
CREATE TABLE nursery_watering_schedule (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    plant_id INTEGER NOT NULL,
    frequency_days INTEGER DEFAULT 3,  -- Frekvence zalévání ve dnech
    last_watered DATE,
    next_watering DATE,
    FOREIGN KEY (plant_id) REFERENCES nursery_plants(id)
);
```

### Tabulka: nursery_watering_log

```sql
CREATE TABLE nursery_watering_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    plant_id INTEGER NOT NULL,
    watered_date DATE NOT NULL,
    amount_liters REAL,                 -- Množství vody v litrech
    watered_by INTEGER,                 -- ID zaměstnance
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (plant_id) REFERENCES nursery_plants(id)
);
```

## API Endpointy

### GET /api/nursery/overview
Vrací přehled statistik a rostlin k zalití dnes.

**Response:**
```json
{
  "success": true,
  "stats": {
    "total_plants": 150,
    "ready_for_sale": 45,
    "growing": 80,
    "dead": 25
  },
  "by_stage": [
    {"stage": "semínko", "count": 20, "total_qty": 500},
    {"stage": "sazenice", "count": 60, "total_qty": 1200},
    {"stage": "prodejní", "count": 45, "total_qty": 800}
  ],
  "watering_today": [
    {
      "id": 1,
      "species": "Echinacea purpurea",
      "location": "Skleník 1",
      "quantity": 50
    }
  ],
  "low_stock": []
}
```

### GET /api/nursery/plants
Vrací seznam všech aktivních rostlin.

**Query parametry:**
- `stage` - Filtr podle fáze (semínko, sazenice, prodejní)

**Response:**
```json
{
  "success": true,
  "plants": [
    {
      "id": 1,
      "species": "Echinacea purpurea",
      "variety": "Magnus",
      "quantity": 50,
      "stage": "prodejní",
      "location": "Skleník 1, Police A3",
      "planted_date": "2024-03-15",
      "purchase_price": 25.50,
      "selling_price": 89.00,
      "notes": "Krásné zdravé rostliny",
      "status": "active",
      "created_at": "2024-03-15T10:00:00",
      "updated_at": "2024-03-20T14:30:00"
    }
  ]
}
```

### POST /api/nursery/plants
Vytvoří novou rostlinu.

**Request body:**
```json
{
  "species": "Echinacea purpurea",
  "variety": "Magnus",
  "quantity": 50,
  "stage": "semínko",
  "location": "Skleník 1",
  "planted_date": "2024-03-15",
  "purchase_price": 25.50,
  "selling_price": 89.00,
  "notes": "První várka"
}
```

**Response:**
```json
{
  "success": true,
  "id": 1
}
```

### PUT /api/nursery/plants/<id>
Upraví existující rostlinu.

**Request body:** Stejný jako POST

**Response:**
```json
{
  "success": true
}
```

### POST /api/nursery/watering
Zaznamená zalití rostliny.

**Request body:**
```json
{
  "plant_id": 1,
  "date": "2024-03-20",
  "amount": 5.0,
  "notes": "Ranní zalévání"
}
```

**Response:**
```json
{
  "success": true
}
```

## UI Features

### Dashboard
- **Statistiky** - Přehled celkových počtů, hodnoty skladu
- **Zalévání dnes** - Seznam rostlin k zalití
- **Nízký stav** - Upozornění na nízký stav prodejních rostlin

### Seznam rostlin
- **Vyhledávání** - Fulltextové vyhledávání podle druhu, odrůdy, lokace
- **Filtry** - Filtrování podle růstové fáze
- **Řazení** - Podle názvu, množství, data zasazení
- **Karty** - Přehledné kartičky s klíčovými informacemi

### Detail rostliny
- Kompletní informace o rostlině
- Historie zalévání
- Možnost úpravy

### Modální okna
- **Přidat rostlinu** - Formulář pro novou rostlinu
- **Upravit rostlinu** - Editace existující rostliny
- **Detail** - Zobrazení všech informací

## Workflow

### 1. Přidání nové rostliny
1. Klikni na "Přidat rostlinu"
2. Vyplň základní údaje (druh, odrůda, množství)
3. Vyber růstovou fázi
4. Zadej lokaci (volitelné)
5. Zadej datum zasazení (volitelné)
6. Zadej ceny (volitelné)
7. Ulož

### 2. Sledování růstu
1. Rostlina začíná jako "semínko"
2. Po vyklíčení změň na "sazenice"
3. Když je připravená k prodeji, změň na "prodejní"

### 3. Zalévání
1. Dashboard zobrazí rostliny k zalití dnes
2. Po zalití klikni na "✓ Zalito"
3. Systém zaznamená zalití a posune další termín

### 4. Prodej
1. Když prodáš rostliny, sniž množství
2. Při prodeji všech kusů změň status na "sold"

## Plánované rozšíření

### 🔄 V přípravě

1. **Hromadné akce**
   - Hromadné změny fází
   - Hromadné přesuny mezi lokacemi

2. **Historie změn**
   - Sledování změn množství
   - Historie přesunů

3. **Fotografie**
   - Přidání fotek k rostlinám
   - Galerie růstových fází

4. **Reporting**
   - Export do PDF/Excel
   - Měsíční přehledy prodeje
   - Analýza ziskovosti

5. **Etikety**
   - Tisk etiket na rostliny
   - QR kódy pro snadnou identifikaci

6. **Objednávky**
   - Napojení na zákaznické objednávky
   - Rezervace rostlin

7. **Inventury**
   - Pravidelné kontroly
   - Automatické upozornění na rozdíly

## Tipy pro používání

### Organizace lokací
Doporučujeme používat strukturovaný systém označení:
- **Skleník 1, Police A1** - Pro malé prostory
- **Školka Venkovní, Záhon 3, Řada 2** - Pro větší plochy
- **Sklad, Box 15** - Pro uskladnění

### Růstové fáze
- **Semínko** - Od zasení po vyklíčení (obvykle 1-3 týdny)
- **Sazenice** - Od vyklíčení po dosažení prodejní velikosti (2-8 měsíců)
- **Prodejní** - Připraveno k prodeji

### Ceny
- **Nákupní cena** - Zadej celkovou cenu za semínka/výsevy děleno počtem kusů
- **Prodejní cena** - Nastav podle velikosti a druhu rostliny

### Zalévání
- Nastav frekvenci podle druhu (sukulenty 7-10 dní, ostatní 2-3 dny)
- Systém automaticky upozorní na rostliny k zalití

## Troubleshooting

### Rostliny se nezobrazují
1. Zkontroluj filtr (může být aktivní)
2. Zkontroluj vyhledávání (může být zadaný text)
3. Refresh stránku (F5)

### Statistiky nesedí
1. Zkontroluj, zda nejsou zastaralé data (status='dead' se nepočítá)
2. Refresh cache v prohlížeči

### Chyba při ukládání
1. Zkontroluj povinná pole (druh, množství, fáze)
2. Zkontroluj formát dat (datum, čísla)

## Changelog

### v1.0 (2025-01-29)
- ✅ Základní správa rostlin (CRUD)
- ✅ Růstové fáze
- ✅ Zalévání
- ✅ Statistiky
- ✅ Vyhledávání a filtry
- ✅ Responzivní design
- ✅ Dark mode

---

**Autor:** Green David Team  
**Poslední update:** 29.1.2025
