
green david app — Tlačítko „Upravit“ u zakázek
===============================================

Co to dělá
----------
- Přidává tlačítko **Upravit** do:
  1) **Detailu zakázky** (vedle „← Zpět na seznam“) — přesměruje na `/job_edit.html?id=<ID>`.
  2) **Karet v seznamu zakázek** — pokusí se zjistit ID a otevřít `/job_edit.html?id=<ID>`.

Jak nasadit
-----------
1) Nahrajte soubor **inject_edit_button.js** do kořene statických souborů (tam, kde je `index.html`).  
2) V souboru **index.html** přidejte před `</body>` tento řádek:

   ```html
   <script src="/inject_edit_button.js"></script>
   ```

   (soubor **index_inject_snippet.html** obsahuje přesně tento řádek pro copy‑paste).

Poznámky
--------
- Detail zakázky bere **ID** spolehlivě z odkazu „Export XLSX“ (`job_id` v URL) a tlačítko
  „Upravit“ se zobrazí vždy.  
- U karet v seznamu je ID dostupné až po kliknutí na „Otevřít detail“. Proto je tam
  „Upravit“ řešeno tak, že dočasně zachytí první volání `fetch('/api/jobs/<id>')`,
  z něj zjistí ID a rovnou vás přesměruje na `/job_edit.html?id=<id>`.
  Když se ID nepodaří zjistit (např. jiná verze renderu), zobrazí se srozumitelná hláška.

Kompatibilita
-------------
- Nezasahuje do existujícího React/JSX kódu — jen pozoruje DOM.  
- Bezpečné pro budoucí změny rozvržení; případné úpravy vyžadují jen úpravu selektorů ve `inject_edit_button.js`.
