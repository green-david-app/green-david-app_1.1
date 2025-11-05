Fix #2: hlavička zachována, žádné záložky navíc

- Tento layout vychází z původního `layout.html` v repu.
- Neobsahuje <div class="tabs"> ani JS injektor záložek.
- Přidává jen CSS a JS pro globální vyhledávání (nezasahuje do headeru).
- Vše ostatní nechává přesně jako dřív.

Nasazení: přepište `templates/layout.html` tímto souborem.
