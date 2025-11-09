
# Calendar backend fix — 2025-11-09

## Co je uvnitř
- `migrations/2025-11-09_fix_tasks_created_at.sql` — zrebuilduje tabulku `tasks` tak, aby `created_at` mělo DEFAULT `CURRENT_TIMESTAMP` a vloží se i tam, kde dřív chybělo.
- `run_migration.py` — jednoduchý skript, který migraci spustí nad vaším `data.db`.
- `main_api_tasks_snippet.py` — hotový blok pro endpoint `/api/tasks`, který při POST doplní `created_at` na straně serveru a zjednodušuje PATCH/DELETE.

## Doporučený postup (drop-in)
1. Nakopírujte složku do repa, třeba jako `backend_patches/`.
2. **Jednorázově** spusťte migraci:
   ```bash
   cd backend_patches
   python3 run_migration.py ../data.db
   ```
   (případně upravte cestu k vaší SQLite DB)

3. Otevřete svůj `main.py` a nahraďte tělo endpointu `/api/tasks` obsahem z `main_api_tasks_snippet.py` (blok mezi `BEGIN/END PATCH`).  
   → Pokud už máte route definovanou, stačí nahradit pouze logiku pro POST/PATCH/DELETE.

4. Deployni — frontend `calendar.html` už očekává tyto změny.

Pozn.: SQLite neumí jednoduše změnit `DEFAULT`/`NOT NULL` u existujícího sloupce, proto migrace tabulku korektně přestaví a data zachová.
