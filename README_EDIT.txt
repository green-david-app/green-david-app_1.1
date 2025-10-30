
green david app — Úprava zakázek (editace)
==========================================

Co to dělá
----------
Přidává samostatnou stránku **/job_edit.html**, přes kterou lze zakázku upravit
(název, zákazník, stav, město, kód, datum, poznámka). Funguje nad existujícím
backendem: načte detail přes **GET /api/jobs/<id>** a ukládá změny přes
**PATCH /api/jobs** (server si sám znormalizuje datum).

Použití
-------
1) Přihlas se do aplikace (aby byl v `localStorage` token `gd_token`).  
2) Otevři URL ve tvaru: `/job_edit.html?id=123`  
   (ID zakázky zjistíš z přehledu Zakázky – klikni na detail a koukni do URL
   volání API nebo do exportu; případně rozšířím o tlačítko přímo v detailu).

Nasazení
--------
- Nahraj `job_edit.html` do kořene statických souborů (tam, kde je `index.html`).

Poznámky
--------
- Datum se na serveru převádí na `YYYY-MM-DD` – stránka posílá `YYYY-MM-DD`
  sama (nebo korektně převede `DD.MM.RRRR`).
- Pokud budeš chtít, přidám tlačítko „Upravit“ přímo do detailu zakázky
  (v `index.html`), které tě sem přesměruje s příslušným `id`.
