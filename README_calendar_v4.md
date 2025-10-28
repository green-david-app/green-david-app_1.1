# green david app – Calendar v4 (iPhone‑like)
- čitelné na mobilu: v buňce max 2 "pilulky", zbytek v přehledném sheetu po klepnutí
- žádné horizontální rozjíždění (minmax(0,1fr), width:100%, overflow-x:hidden)
- desktop má rozumné boční odsazení (container max-width + padding)
- funguje jak pro statický `/calendar.html` (tenhle soubor), tak pro Flask šablonu (`app/static/css/app.css`)

## Nasazení
Nahraď tyto soubory v repu:
- `/calendar.html`
- `/style.css`
- `/static/style.css` (pokud používáš)
- `/app/static/css/app.css`

Commit + deploy na Renderu.
