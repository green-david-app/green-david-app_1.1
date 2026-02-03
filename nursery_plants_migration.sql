-- Rozšíření tabulky nursery_plants o botanické údaje z katalogu
-- Spusť jen pokud tabulka nursery_plants už existuje a chybí jí tyto sloupce

-- Zkontroluj, zda tabulka existuje
-- sqlite3 instance/green_david.db ".schema nursery_plants"

-- Přidání botanických sloupců (pokud neexistují)
-- POZOR: Toto může selhat, pokud sloupce už existují - to je OK

ALTER TABLE nursery_plants ADD COLUMN flower_color TEXT;
ALTER TABLE nursery_plants ADD COLUMN flowering_time TEXT;
ALTER TABLE nursery_plants ADD COLUMN height TEXT;
ALTER TABLE nursery_plants ADD COLUMN light_requirements TEXT;
ALTER TABLE nursery_plants ADD COLUMN leaf_color TEXT;
ALTER TABLE nursery_plants ADD COLUMN hardiness_zone TEXT;
ALTER TABLE nursery_plants ADD COLUMN site_type TEXT;
ALTER TABLE nursery_plants ADD COLUMN plants_per_m2 TEXT;
ALTER TABLE nursery_plants ADD COLUMN botanical_notes TEXT;

-- Pokud tabulka nursery_plants ještě neexistuje, vytvoř ji kompletní:

CREATE TABLE IF NOT EXISTS nursery_plants (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    
    -- Základní identifikace
    latin_name TEXT NOT NULL,
    variety TEXT,
    container_size TEXT,
    
    -- Botanické údaje (z katalogu)
    flower_color TEXT,
    flowering_time TEXT,
    height TEXT,
    light_requirements TEXT,
    leaf_color TEXT,
    hardiness_zone TEXT,
    site_type TEXT,
    plants_per_m2 TEXT,
    botanical_notes TEXT,
    
    -- Školkařské údaje
    count INTEGER NOT NULL DEFAULT 0,
    location TEXT,
    status TEXT DEFAULT 'sazenice',  -- semínko, sazenice, prodejní
    price REAL,
    planted_date DATE,
    harvest_date DATE,
    
    -- Šarže/batch
    batch_id TEXT,
    supplier TEXT,
    
    -- Metadata
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by INTEGER,
    
    -- Poznámky specifické pro tento kus/šarži (ne botanické)
    notes TEXT,
    
    FOREIGN KEY (created_by) REFERENCES users(id)
);

-- Indexy pro rychlejší vyhledávání
CREATE INDEX IF NOT EXISTS idx_nursery_plants_latin ON nursery_plants(latin_name);
CREATE INDEX IF NOT EXISTS idx_nursery_plants_status ON nursery_plants(status);
CREATE INDEX IF NOT EXISTS idx_nursery_plants_location ON nursery_plants(location);
CREATE INDEX IF NOT EXISTS idx_nursery_plants_batch ON nursery_plants(batch_id);

-- Trigger pro automatickou aktualizaci updated_at
CREATE TRIGGER IF NOT EXISTS nursery_plants_update_timestamp 
AFTER UPDATE ON nursery_plants
BEGIN
    UPDATE nursery_plants SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;
