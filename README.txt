Fix: odstranění rozbité hlavičky/záložek

Co to dělá
- Nahrazuje pouze templates/layout.html tak, aby:
  - NEVKLÁDAL žádné „Kalendář / Výkazy hodin“ záložky.
  - ponechal vaši původní horní lištu a navigaci bez zásahů.
  - jen načítal CSS a skript pro globální vyhledávání (které nijak nemění header).

Nasazení
1) Přepište soubor templates/layout.html tímto z balíčku.
2) Není potřeba měnit žádné jiné soubory.
