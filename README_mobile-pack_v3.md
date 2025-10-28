# green david app – Mobile pack v3
Tento balíček opravuje rozjíždění kalendáře na mobilech pro všechny varianty:
- Statická stránka `/calendar.html` (používá `/style.css`)
- Starší statická téma `/static/style.css`
- Flask/Jinja varianta (`app/templates/*` + `app/static/css/app.css`)

## Co vyměnit v repu
1. Nahraď soubor na kořeni: `/style.css`
2. Pokud existuje, nahraď i `/static/style.css` (starší nasazení)
3. Nahraď `/calendar.html` (kořen)
4. Nahraď `/app/static/css/app.css` (pro Flask šablonu)
Poté commit + push a redeploy na Renderu.

## Co je opraveno
- Všechny ovládací prvky se zalamují, žádný pevný min-width na štítku měsíce.
- Mřížka používá `repeat(7, minmax(0,1fr)) + width:100%`, takže se neveze mimo viewport.
- Texty událostí se zkrátí pomocí `text-overflow: ellipsis` a nemohou roztáhnout buňku.
- Globálně zakázaný horizontální scroll (`overflow-x:hidden`).

