Hotfix – přidání záložky "Brigádníci" do horní lišty

1) Nahrajte oba soubory do kořene webu (tam, kde je index.html):
   - brigadnici-tab.js
   - index.inject.html

2) Soubor index.inject.html je miniaturní fragment, který pouze vkládá <script src="/brigadnici-tab.js" defer></script>.
   Pokud máte přístup k index.html, stačí ten řádek přidat těsně před </body> a soubor index.inject.html nepotřebujete.

Tento hotfix pouze doplní odkaz do existující lišty Tabs a je bezpečný i při re-renderu (kontroluje duplicitní vložení).
