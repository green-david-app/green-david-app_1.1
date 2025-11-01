
green david app — FIX: správné zadání data u nové zakázky
=========================================================

Co je opraveno
--------------
- Přidán povinný vstup **Datum** do šablony **templates/jobs_edit.html**.
  Při vytváření/úpravě zakázky se tak datum odešle na backend, který ho
  už správně normalizuje na formát YYYY-MM-DD pomocí `_normalize_date`.

Proč je to potřeba
------------------
- V API pro zakázky (`POST /api/jobs`) se pole `date` očekává a na serveru
  se přenormuje na ISO (YYYY-MM-DD). Pokud ho UI neposlalo, mohlo docházet
  k uložení špatného či prázdného data, případně k pádu validace.

Související poznámky
--------------------
- Kalendářové API `/gd/api/calendar` už má hotfix, který také používá
  `_normalize_date` pro jakékoliv datum (včetně `DD.MM.YYYY`).

Nasazení
--------
1. Nahraďte soubor `templates/jobs_edit.html` tímto z balíčku.
2. Restartujte aplikaci / službu na Renderu.

Kontrola
--------
- Otevřete **Zakázky → Nová zakázka** a vyplňte datum. Po uložení by měla
  mít nová zakázka správné datum a případně se správně propsat i do kalendáře
  (pokud ho zobrazujete skrze virtualizované job události).
