Patch pro sjednocení designu „Výkazy hodin“ s hlavní aplikací:

1) main.py
   - Přidána routa /timesheets, která renderuje templates/timesheets.html (design z layoutu).
   - Starý /timesheets.html přesměrován 301 na /timesheets.

2) templates/timesheets.html
   - Jinja šablona dědí z layout.html, styly a komponenty jako z aplikace.
   - Týdenní pohled + modální okno pro přidání/úpravu záznamu.

3) index.html
   - V komponentě Tabs změňte odkaz z /timesheets.html na /timesheets.
     (viz soubor index_patch_hints níže)

4) Smazat/nepoužívat starý kořenový soubor timesheets.html (ten tmavý samostatný).

Nasazení:
- Nahraďte uvedené soubory ve vašem projektu a restartujte aplikaci.
- Ověřte v navigaci „Výkazy“ → URL je /timesheets a vzhled odpovídá zbytku appky.
