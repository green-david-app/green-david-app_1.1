POSTUP ÚPRAV BACKENDU (main.py)
--------------------------------
1) Přidejte `import re` (pokud chybí).
2) Vložte route pro /api/jobs/<int:jid> (viz blok výše).
3) Vložte proxy route /gd/api/jobs (viz blok výše).
4) V `api_jobs()` nahraďte DELETE větev za uvedenou verzi.
5) Nasadit na Render.

FRONTEND
--------
- Ujistěte se, že se na stránce se seznamem Zakázek načítá:
  <script src="/static/patch/jobs-patch.js"></script>