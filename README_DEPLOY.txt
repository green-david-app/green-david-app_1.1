GREEN-DAVID – PATCH: robustní mazání zakázek (backend + UI fallback)
===================================================================

Co je v balíčku
---------------
1) static/patch/jobs-patch.js
   - Frontendový "chytrý" deleter pro Zakázky: volá DELETE /api/jobs/<id>,
     při 409 se zeptá na kaskádu a případně zavolá ?force=1.
     Pokud by path route neexistovala, zkusí fallback /api/jobs?id=<id>.

2) server_patch/main_delete_blocks.txt
   - Hotový kód bloků pro main.py (DELETE /api/jobs, DELETE /api/jobs/<id>,
     proxy /gd/api/jobs) – vložte do vašeho main.py dle níže uvedených kroků.
   - Kód je psaný tak, aby fungoval s existujícími pomocnými funkcemi:
     get_db(), require_role(), jsonify, request atd.

3) server_patch/README_APPLY.txt
   - Stručný postup, kam co vložit.

Co udělat po nahrání
--------------------
A) BACKEND
   1. Otevřete váš main.py
   2. Ujistěte se, že nahoře máte:  `import re`
   3. Do main.py doplňte tři věci (viz server_patch/main_delete_blocks.txt):
      - ROUTE: /api/jobs/<int:jid>  (mazání jedné zakázky přes path)
      - ROUTE: /gd/api/jobs         (proxy na api_jobs DELETE)
      - V `api_jobs()` nahraďte / doplňte větev `if request.method == "DELETE":`
        za verzi z tohoto balíčku (tolerantní parsování id + force kaskáda)
   4. Nasadit (Render build & deploy).

B) FRONTEND
   1. Zajistěte, aby se na stránce se seznamem Zakázek načetl soubor:
      <script src="/static/patch/jobs-patch.js"></script>
      (vložit za ostatní skripty; pokud máte šablonu, přidejte řádek do ní).
   2. Hotovo – UI už používá chytré mazání a umí fallback na force=1.

Rychlý test
-----------
- Bez vazeb:
  curl -i -X DELETE "https://…/api/jobs/7"           → 200 {"ok":true}

- Se starým stylem id (pro klid duše):
  curl -i -X DELETE "https://…/api/jobs?id=job-7"    → 200/409

- S vazbami:
  curl -i -X DELETE "https://…/api/jobs/10"          → 409 + počty
  curl -i -X DELETE "https://…/api/jobs/10?force=1"  → 200 {"ok":true}