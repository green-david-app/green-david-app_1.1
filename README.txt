green david app — Mobile overflow fix
====================================

Co je v balíčku
---------------
- app/templates/base.html — doplněn řádek s mobile-lock.css

Instrukce
---------
1) Nahraj do repa obsah tohoto ZIPu tak, aby soubor nahradil existující `app/templates/base.html`.
2) Ujisti se, že v repu existuje soubor `/static/assets/mobile-lock.css` (v tvé codebase už je).
3) Restartuj aplikaci (Render re-deploy, nebo restart služby).

Ověření
-------
- Otevři kalendář a výkazy na mobilu (šířka < 768px).
- Nesmí být horizontální posuvník a layout se nesmí "rozlézat".
