GREEN-DAVID – PATCH v2 (definitivní)
====================================
Co opravuje:
- 400 při DELETE /api/jobs?id=7 (tolerantní parsování id z query/JSON i "job-7").
- 409 u zakázek s vazbami: nově podpora `?force=1` (smaže tasks + timesheets).
- Chybějící route: přidává **/api/jobs/<int:id>** (path) + **/gd/api/jobs** (proxy).
- Frontend autoload: přidá chytré mazání i když na stránce není ručně vložený script.

Co nahrát:
- `server_patch/main_delete_blocks_v2.txt` – vlož do `main.py` (viz níže).
- `static/patch/jobs-patch.js` – JS pro chytré mazání.
- `static/patch/autoload-patch.js` – automaticky „přilepí“ jobs‑patch na všech stránkách.

Jak to aktivovat bez editace šablon:
1) **Načti autoload:** do hlavičky (kde už načítáš `/static/patch/override.css` nebo `calendar-patch.js`) přidej
   `<script src="/static/patch/autoload-patch.js?v=20251017"></script>`
   (ideálně do společného layoutu, aby platilo pro `/` i `/calendar.html`).
2) Backend uprav podle `server_patch/README_APPLY_v2.txt`.
