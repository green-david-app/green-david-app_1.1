# Unifikace kalendáře (jednoduché a funkční jako na iPhonu)
Tento patch sjednocuje kalendář na **jediný zdroj**:
- Aplikace používá `app/templates/calendar.html` + `app/static/js/calendar.js`.
- JS obsahuje iPhone-like klik na den (`openDaySheet`) a lokální datový klíč (`tzIso`) pro spolehlivé párování událostí.
- **Žádné globální CSS změny**, jen kalendář.

## Kroky
1) Nahraď v repu soubory z tohoto ZIPu:
   - `app/templates/calendar.html`
   - `app/static/js/calendar.js`
2) Commit & deploy.

## Doporučený úklid (volitelné, jednorázově)
Aby se to už nemíchalo, odstraň/nepoužívej duplicity:
- `static/js/calendar.js`
- `templates/calendar.html`

A ponech jen `app/*` variantu.
