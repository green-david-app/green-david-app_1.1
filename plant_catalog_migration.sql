-- Tabulka pro katalog rostlin (botanické údaje)
CREATE TABLE IF NOT EXISTS plant_catalog (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    latin_name TEXT NOT NULL,              -- Název bez odrůdy, např. "Aquilegia caerulea"
    variety TEXT,                          -- Odrůda, např. "Blue Star"
    container_size TEXT,                   -- Velikost kontejneru, např. "K9"
    flower_color TEXT,                     -- Barva květu
    flowering_time TEXT,                   -- Doba květu, např. "5-6"
    leaf_color TEXT,                       -- Barva listu
    height TEXT,                           -- Výška v době květu
    light_requirements TEXT,               -- Nároky na světlo
    site_type TEXT,                        -- Stanoviště (Fr, GR, B, St...)
    plants_per_m2 TEXT,                    -- Počet ks na m2
    hardiness_zone TEXT,                   -- Zona mrazuvzdornost
    notes TEXT,                            -- Specifikum/poznámky
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(latin_name, variety)            -- Kombinace musí být unikátní
);

-- Index pro rychlejší vyhledávání
CREATE INDEX IF NOT EXISTS idx_plant_catalog_latin ON plant_catalog(latin_name);
CREATE INDEX IF NOT EXISTS idx_plant_catalog_variety ON plant_catalog(variety);

-- Full-text search index pro vyhledávání
CREATE VIRTUAL TABLE IF NOT EXISTS plant_catalog_fts USING fts5(
    latin_name,
    variety,
    flower_color,
    notes,
    content=plant_catalog,
    content_rowid=id
);

-- Trigger pro automatickou aktualizaci FTS
CREATE TRIGGER IF NOT EXISTS plant_catalog_ai AFTER INSERT ON plant_catalog BEGIN
    INSERT INTO plant_catalog_fts(rowid, latin_name, variety, flower_color, notes)
    VALUES (new.id, new.latin_name, new.variety, new.flower_color, new.notes);
END;

CREATE TRIGGER IF NOT EXISTS plant_catalog_ad AFTER DELETE ON plant_catalog BEGIN
    DELETE FROM plant_catalog_fts WHERE rowid = old.id;
END;

CREATE TRIGGER IF NOT EXISTS plant_catalog_au AFTER UPDATE ON plant_catalog BEGIN
    UPDATE plant_catalog_fts SET 
        latin_name = new.latin_name,
        variety = new.variety,
        flower_color = new.flower_color,
        notes = new.notes
    WHERE rowid = new.id;
END;
