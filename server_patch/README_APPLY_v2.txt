POSTUP ÚPRAV BACKENDU (main.py)
--------------------------------
1) Doplň `import re` (pokud chybí).
2) Vlož *nad* definici `api_jobs()` nové bloky z `main_delete_blocks_v2.txt`:
   - route `DELETE /api/jobs/<int:jid>`
   - route `DELETE /gd/api/jobs`
   - pomocné funkce `_parse_job_id` + `_delete_job_impl`
3) Uvnitř `api_jobs()` NAHRAĎ sekci `if request.method == "DELETE":` uvedeným blokem.
4) Deploy na Render.

FRONTEND (bez šahání do šablon, 1 řádek)
----------------------------------------
Vlož **jediný řádek** do společného layoutu (nebo na obě stránky `/` a `/calendar.html`):
<script src="/static/patch/autoload-patch.js?v=20251017"></script>

Tím se automaticky načte `/static/patch/jobs-patch.js` podle obsahu stránky.

TESTY
-----
- DELETE /api/jobs/7                → 200 {"ok":true}
- DELETE /api/jobs?id=job-7         → 200 {"ok":true}
- DELETE /gd/api/jobs?id=7          → 200 {"ok":true}
- DELETE /api/jobs/10               → 409 + počty; následně ?force=1 → 200
