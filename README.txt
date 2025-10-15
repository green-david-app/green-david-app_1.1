green david app · MOBILE PACK (responsive + footer + export)

Soubory (nahraj do kořene projektu):
- mobile-override.css  → responzivní vzhled (kalendář, tabulky, modály)
- common-footer.js     → lepící footer s „Přihlášen: …“ a auto-načtení CSS
- calendar.html        → kalendář s mobile úpravami (volá /gd/api/calendar)
- timesheets.html      → výkazy s filtry a exportem CSV/XLSX (volá /gd/api/timesheets, /gd/api/employees, /api/jobs)

Zapnutí na ostatních stránkách:
Před </body> stačí vložit  <script src="/common-footer.js" defer></script>
CSS se případně připojí automaticky.

Poznámky:
- Mazání výkazů je jen pro uživatele s e‑mailem v doménách @greendavid.cz a @greendavid.local (ostatní mohou přidávat).
- Footer čte /api/me. Na mobilu je sticky u spodního okraje (safe‑area iOS).
