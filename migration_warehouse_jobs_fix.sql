-- ============================================================================
-- MIGRACE: Oprava propojení skladu a zakázek
-- ============================================================================
-- Tato migrace opravuje problém s nefunkčním propojením skladu a zakázek
--
-- Změny:
-- 1. Přidá reserved_qty sloupec do warehouse_items
-- 2. Přidá sloupce do job_materials pro propojení se skladem
-- 3. Vytvoří trigger pro automatické počítání rezervovaného množství
-- ============================================================================

-- Krok 1: Přidat reserved_qty do warehouse_items pokud tam ještě není
-- ============================================================================
ALTER TABLE warehouse_items ADD COLUMN reserved_qty REAL DEFAULT 0;

-- Krok 2: Rozšířit job_materials tabulku
-- ============================================================================
-- Přidat sloupce pro propojení se skladem
ALTER TABLE job_materials ADD COLUMN warehouse_item_id INTEGER;
ALTER TABLE job_materials ADD COLUMN reserved_qty REAL DEFAULT 0;
ALTER TABLE job_materials ADD COLUMN warehouse_location TEXT DEFAULT '';
ALTER TABLE job_materials ADD COLUMN status TEXT DEFAULT 'planned' CHECK(status IN ('planned', 'ordered', 'delivered', 'used'));

-- Přidat foreign key index
CREATE INDEX IF NOT EXISTS idx_job_materials_warehouse ON job_materials(warehouse_item_id);

-- Krok 3: Přepočítat existující rezervace
-- ============================================================================
-- Aktualizuj reserved_qty ve warehouse_items na základě existujících job_materials
UPDATE warehouse_items
SET reserved_qty = (
    SELECT COALESCE(SUM(jm.qty), 0)
    FROM job_materials jm
    WHERE jm.warehouse_item_id = warehouse_items.id
    AND jm.status IN ('planned', 'ordered')
)
WHERE id IN (
    SELECT DISTINCT warehouse_item_id 
    FROM job_materials 
    WHERE warehouse_item_id IS NOT NULL
);

-- Krok 4: Trigger pro automatickou aktualizaci rezervací
-- ============================================================================
-- Když se přidá/upraví materiál v zakázce, aktualizuj reserved_qty ve skladu

DROP TRIGGER IF EXISTS trg_job_materials_reserve_insert;
CREATE TRIGGER trg_job_materials_reserve_insert
AFTER INSERT ON job_materials
WHEN NEW.warehouse_item_id IS NOT NULL AND NEW.status IN ('planned', 'ordered')
BEGIN
    UPDATE warehouse_items
    SET reserved_qty = reserved_qty + NEW.qty,
        updated_at = datetime('now')
    WHERE id = NEW.warehouse_item_id;
END;

DROP TRIGGER IF EXISTS trg_job_materials_reserve_update;
CREATE TRIGGER trg_job_materials_reserve_update
AFTER UPDATE ON job_materials
WHEN NEW.warehouse_item_id IS NOT NULL
BEGIN
    -- Odečti staré množství (pokud bylo rezervované)
    UPDATE warehouse_items
    SET reserved_qty = reserved_qty - CASE 
        WHEN OLD.status IN ('planned', 'ordered') THEN OLD.qty 
        ELSE 0 
    END,
    updated_at = datetime('now')
    WHERE id = OLD.warehouse_item_id;
    
    -- Přičti nové množství (pokud je rezervované)
    UPDATE warehouse_items
    SET reserved_qty = reserved_qty + CASE 
        WHEN NEW.status IN ('planned', 'ordered') THEN NEW.qty 
        ELSE 0 
    END,
    updated_at = datetime('now')
    WHERE id = NEW.warehouse_item_id;
END;

DROP TRIGGER IF EXISTS trg_job_materials_reserve_delete;
CREATE TRIGGER trg_job_materials_reserve_delete
AFTER DELETE ON job_materials
WHEN OLD.warehouse_item_id IS NOT NULL AND OLD.status IN ('planned', 'ordered')
BEGIN
    UPDATE warehouse_items
    SET reserved_qty = reserved_qty - OLD.qty,
        updated_at = datetime('now')
    WHERE id = OLD.warehouse_item_id;
END;

-- ============================================================================
-- HOTOVO
-- ============================================================================
-- Po spuštění této migrace:
-- 1. reserved_qty bude správně sledovat rezervovaná množství
-- 2. Při přidání materiálu do zakázky se automaticky rezervuje ze skladu
-- 3. Při smazání materiálu ze zakázky se automaticky uvolní rezervace
-- 4. V seznamu skladu půjde vidět, kolik je rezervováno
-- ============================================================================
