green-david app – login fix + robustní výkazy (PATCH)
====================================================

Co je uvnitř
------------
- main.py – nový server:
  - správná konfigurace session cookies (Secure + SameSite=None + permanentní)
  - ProxyFix (Render reverse proxy)
  - /api/login, /api/logout, /api/me
  - /api/jobs (GET/POST), /api/employees (GET/POST), /api/timesheets (GET/POST)
  - tolerantní parsování výkazů (CZ/EN názvy polí, 8 / 8,0 / 8.5 ...)

Jak použít
----------
1) Nahraď ve svém projektu soubor **main.py** tímto z patche.
2) Nasadit / restartovat Render službu.

Poznámka
--------
Data se zapisují do složky `data/` (jobs.json, employees.json, timesheets.json).
Pokud soubory existují, zůstanou zachované.
