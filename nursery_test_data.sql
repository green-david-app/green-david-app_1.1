-- Testovací data pro Nursery modul
-- Spustit: python3 -c "import sqlite3; conn = sqlite3.connect('app.db'); conn.executescript(open('nursery_test_data.sql').read()); conn.commit()"

-- Semínka (čerstvě zasazené)
INSERT INTO nursery_plants (species, variety, quantity, stage, location, planted_date, purchase_price, selling_price, notes, status) VALUES
('Echinacea purpurea', 'Magnus', 200, 'semínko', 'Skleník 1, Stůl A', '2025-01-15', 0.50, 89.00, 'První várka letošního roku', 'active'),
('Rudbeckia fulgida', 'Goldsturm', 150, 'semínko', 'Skleník 1, Stůl B', '2025-01-20', 0.45, 79.00, 'Velmi oblíbená odrůda', 'active'),
('Salvia nemorosa', 'Caradonna', 100, 'semínko', 'Skleník 2, Police 1', '2025-01-22', 0.60, 95.00, 'Tmavě fialové květy', 'active'),
('Heuchera', 'Palace Purple', 80, 'semínko', 'Skleník 2, Police 2', '2025-01-25', 0.80, 120.00, 'Dekorativní listy', 'active');

-- Sazenice (ve fázi růstu)
INSERT INTO nursery_plants (species, variety, quantity, stage, location, planted_date, purchase_price, selling_price, notes, status) VALUES
('Aster novi-belgii', 'Marie Ballard', 120, 'sazenice', 'Skleník 1, Záhon 1', '2024-11-10', 0.40, 85.00, 'Dobře zakořeněné', 'active'),
('Phlox paniculata', 'Blue Paradise', 95, 'sazenice', 'Skleník 1, Záhon 2', '2024-11-15', 0.55, 95.00, 'Již mají 4-5 lístků', 'active'),
('Coreopsis verticillata', 'Moonbeam', 110, 'sazenice', 'Skleník 3, Stůl C', '2024-12-01', 0.35, 75.00, 'Rychlý růst', 'active'),
('Geranium', 'Rozanne', 75, 'sazenice', 'Skleník 3, Police 3', '2024-12-05', 0.90, 135.00, 'Prémiová odrůda', 'active'),
('Nepeta faassenii', 'Walkers Low', 130, 'sazenice', 'Venkovní školka, Záhon A', '2024-11-20', 0.30, 69.00, 'Otužené proti mrazu', 'active'),
('Iris sibirica', 'Caesar Brother', 60, 'sazenice', 'Venkovní školka, Záhon B', '2024-11-25', 0.70, 110.00, 'Silné kořeny', 'active');

-- Prodejní (připravené k prodeji)
INSERT INTO nursery_plants (species, variety, quantity, stage, location, planted_date, purchase_price, selling_price, notes, status) VALUES
('Lavandula angustifolia', 'Hidcote', 45, 'prodejní', 'Prodejní stůl 1', '2024-09-15', 0.40, 89.00, 'BESTSELLER', 'active'),
('Sedum spectabile', 'Autumn Joy', 38, 'prodejní', 'Prodejní stůl 1', '2024-09-20', 0.35, 75.00, 'Ihned k prodeji', 'active'),
('Achillea millefolium', 'Cerise Queen', 52, 'prodejní', 'Prodejní stůl 2', '2024-09-10', 0.30, 69.00, 'Zdravé rostliny', 'active'),
('Delphinium', 'Pacific Giants Mix', 25, 'prodejní', 'Prodejní stůl 2', '2024-08-25', 0.85, 145.00, 'Vysoké odrůdy', 'active'),
('Hosta', 'Sum and Substance', 32, 'prodejní', 'Prodejní stůl 3', '2024-09-05', 1.20, 195.00, 'Velké zlatožluté listy', 'active'),
('Astilbe', 'Bridal Veil', 28, 'prodejní', 'Prodejní stůl 3', '2024-09-12', 0.75, 125.00, 'Bílé květy', 'active'),
('Dianthus', 'Pink Kisses', 65, 'prodejní', 'Prodejní stůl 4', '2024-10-01', 0.25, 59.00, 'Kompaktní růst', 'active'),
('Hemerocallis', 'Stella de Oro', 41, 'prodejní', 'Prodejní stůl 4', '2024-09-18', 0.60, 99.00, 'Opakovaně kvetoucí', 'active'),
('Veronica spicata', 'Royal Candles', 8, 'prodejní', 'Prodejní stůl 5', '2024-10-05', 0.40, 79.00, 'POSLEDNÍ KUSY!', 'active');

-- Nastavení plánů zalévání pro všechny aktivní rostliny
-- Semínka - zalévat každé 2 dny
INSERT INTO nursery_watering_schedule (plant_id, frequency_days, last_watered, next_watering)
SELECT id, 2, date('now', '-1 day'), date('now', '+1 day')
FROM nursery_plants 
WHERE stage = 'semínko' AND status = 'active';

-- Sazenice - zalévat každé 3 dny
INSERT INTO nursery_watering_schedule (plant_id, frequency_days, last_watered, next_watering)
SELECT id, 3, date('now', '-2 days'), date('now', '+1 day')
FROM nursery_plants 
WHERE stage = 'sazenice' AND status = 'active';

-- Prodejní - zalévat každé 4 dny
INSERT INTO nursery_watering_schedule (plant_id, frequency_days, last_watered, next_watering)
SELECT id, 4, date('now', '-3 days'), date('now', '+1 day')
FROM nursery_plants 
WHERE stage = 'prodejní' AND status = 'active';

-- Nějaké rostliny potřebují zalití dnes (pro testování)
UPDATE nursery_watering_schedule 
SET next_watering = date('now')
WHERE plant_id IN (
    SELECT id FROM nursery_plants 
    WHERE species IN ('Echinacea purpurea', 'Lavandula angustifolia', 'Aster novi-belgii')
    LIMIT 3
);

-- Historie zalévání (poslední měsíc)
INSERT INTO nursery_watering_log (plant_id, watered_date, amount_liters, watered_by, notes)
SELECT 
    id,
    date('now', '-' || (abs(random() % 20) + 1) || ' days'),
    round(abs(random() % 10) + 3, 1),
    1,
    CASE abs(random() % 3)
        WHEN 0 THEN 'Ranní zalévání'
        WHEN 1 THEN 'Odpolední zalévání'
        ELSE 'Večerní zalévání'
    END
FROM nursery_plants 
WHERE status = 'active'
ORDER BY random()
LIMIT 30;

-- Výpis přehledu
SELECT 
    '=== PŘEHLED NURSERY ===' as info;

SELECT 
    stage as 'Fáze',
    COUNT(*) as 'Počet druhů',
    SUM(quantity) as 'Celkem kusů',
    ROUND(AVG(selling_price), 2) as 'Průměrná cena'
FROM nursery_plants
WHERE status = 'active'
GROUP BY stage;

SELECT 
    '=== TOP 5 NEJHODNOTNĚJŠÍCH ===' as info;

SELECT 
    species || COALESCE(' ' || variety, '') as 'Rostlina',
    quantity as 'Ks',
    selling_price as 'Cena/ks',
    quantity * selling_price as 'Hodnota celkem'
FROM nursery_plants
WHERE status = 'active' AND stage = 'prodejní'
ORDER BY quantity * selling_price DESC
LIMIT 5;

SELECT 
    '=== NÍZKÝ STAV (< 10 ks) ===' as info;

SELECT 
    species || COALESCE(' ' || variety, '') as 'Rostlina',
    quantity as 'Zbývá kusů',
    location as 'Lokace'
FROM nursery_plants
WHERE status = 'active' AND stage = 'prodejní' AND quantity < 10
ORDER BY quantity ASC;

SELECT 
    '=== ZALÍT DNES ===' as info;

SELECT 
    np.species || COALESCE(' ' || np.variety, '') as 'Rostlina',
    np.quantity as 'Ks',
    np.location as 'Lokace',
    nws.next_watering as 'Termín'
FROM nursery_plants np
JOIN nursery_watering_schedule nws ON np.id = nws.plant_id
WHERE nws.next_watering <= date('now')
AND np.status = 'active'
ORDER BY nws.next_watering;
