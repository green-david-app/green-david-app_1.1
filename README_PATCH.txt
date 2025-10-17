
GD PATCH – 2025‑10‑17
=====================

Co je to
--------
Drop‑in frontend patch, který opravuje MAZÁNÍ u **Zakázek** a **Kalendáře**:
- Zakázky: chytře zkouší oba tvary endpointů (`/api/jobs/ID` i `/api/jobs?id=ID`), 
  umí zareagovat na **409** a po potvrzení znovu zavolat s `force=1`.
- Kalendář: zvládá mazat **čisté kalendářové řádky** (číslo) i **vázané položky**
  (`job-10`, `task-7`). Po úspěchu provede refresh seznamu.

Co zkopírovat
-------------
1) Celý adresář `static/patch/` vlož do tvého projektu.
2) Do společného layoutu (typicky `templates/layout.html`) těsně před `</head>` přidej:

    <!-- BEGIN: gd patch -->
    <link rel="stylesheet" href="/static/patch/override.css?v=20251017">
    <script src="/static/patch/ui-delete.js?v=20251017" defer></script>
    <script src="/static/patch/calendar-patch.js?v=20251017" defer></script>
    <!-- END: gd patch -->

Pozn.: Pokud stránka Kalendář používá vlastní šablonu mimo layout, vlož stejné 3 řádky
také do `templates/calendar.html` (do `<head>`).

Jak to funguje
--------------
- Na libovolný prvek (tlačítko/link) stačí dát atribut `data-delete`:
    - `data-delete="jobs:10"`  … smaže zakázku **10** (s podporou force)
    - `data-delete="tasks:7"`  … smaže úkol **7**
    - `data-delete="cal:15"`   … smaže kalendářový řádek **15**
    - `data-delete="cal:job-10"` … smaže vazbu na zakázku 10
    - `data-delete="cal:task-7"` … smaže vazbu na úkol 7

- Pro starší značky na kalendáři funguje i `data-cal-delete-id="job-10"` apod.

Hotovo
------
Po kopii a redeployi nemusíš nic dalšího měnit. Patch je nezávislý na backendu
a sám si poradí s rozdílnými tvary endpointů i s `409 -> force=1` retriem.
