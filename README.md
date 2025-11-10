# Frontend patch – tolerantní mazání (404 = už smazáno)

Účel: V backendu teď `DELETE /gd/api/tasks?id=…` vrací **404**, když položka v DB už není.
Tvůj frontend to vyhodnocuje jako "API nedostupné". Tenhle skript chování upraví takto:

- Pro `DELETE /gd/api/tasks` (nebo `/api/tasks`) se **404 přemapuje na úspěch** (`{ ok:true, deleted:id }`),
  aby UI jen zrefrešnulo den a nehlásilo chybu.
- Ostatní requesty nechává beze změn.

## Instalace
1. Zkopíruj `public/js/calendar.delete-polyfill.js` mezi ostatní JS.
2. Do konce `calendar.html` vlož PŘED zavírací `</body>`:
```html
<script src="/js/calendar.delete-polyfill.js"></script>
```
Hotovo – vzhled se nemění, jen zmizí falešné chybové hlášky a den se zrefrešuje.
