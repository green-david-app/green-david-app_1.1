# 🌸 NURSERY MODULE - QUICK START

## Rychlé spuštění (5 minut)

### 1. Ověř instalaci

```bash
# Zkontroluj, že tabulky existují
python3 test_nursery.py
```

Pokud test projde ✅, jsi připraven!

### 2. Nahraj testovací data (volitelné)

```bash
# Naplň databázi ukázkovými rostlinami
python3 << 'EOF'
import sqlite3
conn = sqlite3.connect('app.db')
with open('nursery_test_data.sql', 'r', encoding='utf-8') as f:
    conn.executescript(f.read())
conn.commit()
conn.close()
print("✅ Testovací data načtena")
EOF
```

### 3. Spusť aplikaci

```bash
# Spusť Flask
python3 main.py

# Nebo použij start script
./start_local.sh
```

### 4. Otevři v prohlížeči

```
http://localhost:5005/nursery
```

---

## První kroky

### ✅ Přidej první rostlinu

1. **Klikni na "Přidat rostlinu"**
2. **Vyplň základní údaje:**
   - Druh: `Echinacea purpurea`
   - Odrůda: `Magnus` (volitelné)
   - Množství: `50`
   - Fáze: `semínko`
3. **Klikni "Uložit"**

Gratuluju! 🎉 Máš první rostlinu v evidenci.

### ✅ Nastav lokaci

1. **Klikni na kartu rostliny**
2. **Klikni "Upravit"**
3. **Zadej lokaci:**
   - `Skleník 1, Police A3`
4. **Ulož**

Teď víš, kde rostlina je! 📍

### ✅ Sleduj růst

Když rostlina vyklíčí:
1. **Otevři detail** (klikni na kartu)
2. **Klikni "Upravit"**
3. **Změň fázi** na `sazenice`
4. **Ulož**

Systém automaticky aktualizuje statistiky! 📊

### ✅ Zalévání

1. **Dashboard ti ukáže** rostliny k zalití
2. **Po zalití klikni** "✓ Zalito"
3. **Systém zaznamená** a posune další termín

Už nikdy nezapomeneš zalít! 💧

---

## Užitečné tipy

### 🔍 Vyhledávání
- Zadej název druhu nebo odrůdy
- Funguje okamžitě při psaní
- Hledá i v lokacích

### 🎯 Filtry
- **Všechny** - Zobraz všechny rostliny
- **Semínka** - Jen čerstvě zasazené
- **Sazenice** - Ve fázi růstu
- **Prodejní** - Připravené k prodeji

### 📊 Statistiky
Dashboard zobrazuje:
- Celkový počet rostlin
- Ready na prodej
- V pěstování
- Celková hodnota skladu

### ⚠️ Upozornění
Systém automaticky varuje před:
- Nízkým stavem (< 10 ks)
- Rostlinami k zalití dnes
- Zastaralými daty

---

## Typický pracovní den

### 🌅 Ráno (8:00)
1. Otevři dashboard
2. Zkontroluj "Zalít dnes"
3. Zalévej rostliny
4. Označuj je jako "✓ Zalito"

### 🌞 Přes den
1. Přidávej nové semínka
2. Přesouvej rostliny mezi fázemi
3. Aktualizuj stavy po prodeji

### 🌆 Večer (17:00)
1. Zkontroluj nízké stavy
2. Připrav objednávku nových semen
3. Zkontroluj hodnotu skladu

---

## Časté otázky

### ❓ Jak často zalévat?
- **Semínka**: Každé 2 dny
- **Sazenice**: Každé 3 dny  
- **Prodejní**: Každé 4 dny

Systém ti to připomene!

### ❓ Kdy přesunout do další fáze?
- **Semínko → Sazenice**: Po vyklíčení (1-3 týdny)
- **Sazenice → Prodejní**: Když dosáhne prodejní velikosti (2-8 měsíců)

### ❓ Co s prodanými rostlinami?
Sniž množství. Systém automaticky:
- Aktualizuje statistiky
- Přepočítá hodnotu skladu
- Upozorní na nízký stav

### ❓ Můžu mazat rostliny?
Ano, ale raději změň status na `sold` nebo `dead`.
Historie se zachová pro reporting.

---

## Klávesové zkratky

| Klávesa | Akce |
|---------|------|
| `Esc` | Zavře modální okno |
| `Ctrl+F` | Přejde do vyhledávání |
| `/` | Přejde do vyhledávání |

---

## Potřebuješ pomoc?

📖 **Plná dokumentace:** `NURSERY_README.md`

🐛 **Narazil na chybu?**
1. Zkus refresh (F5)
2. Zkontroluj browser konzoli (F12)
3. Spusť test: `python3 test_nursery.py`

💡 **Nápad na novou funkci?**
Přidej do dokumentace sekci "Feature Requests"

---

**Příjemné pěstování! 🌱**
