
green-david-app – rychlý hotfix pro poznámky v kalendáři
=======================================================

Co je uvnitř:
- calendar-notes-wireup.js — přidá u poznámek skutečný text + tlačítka Upravit / Smazat.
- calendar-tasks-patch.js — jistota, že se POST /gd/api/tasks posílá title z textu poznámky.
- Návod níže.

Instalace
---------
1) Zkopírujte oba JS soubory do kořene, kde je `calendar.html` (nebo do stejné složky se skripty).
2) Do `calendar.html` **pod** existující `<script>` tagy přidejte:

   <script src="calendar-tasks-patch.js"></script>
   <script src="calendar-notes-wireup.js"></script>

3) Proveďte tvrdé obnovení (vyprázdnit cache) v prohlížeči: Safari: ⌥⌘E + ⌘R.

Použití
-------
- V záložce **Poznámka** napište text → **Uložit**.
- V seznamu dne se ukáže text poznámky a vedle něj ✏️ (Upravit) a ✖️ (Smazat).
- Upravit posílá `PATCH /gd/api/tasks` (fields: `description`, `title`), Smazat posílá `DELETE /gd/api/tasks?id=…`.

Poznámka
--------
Hotfix je *jen frontendový*. Nepotřebuje migraci DB ani endpoint `/gd/api/notes`. 
Backend musí mít `/gd/api/tasks` s podporou `POST` (vkládá), `PATCH` (mění podle `id`) a `DELETE` (maže podle `id`).

Datum: 2025-11-08T22:04:16.725506Z
