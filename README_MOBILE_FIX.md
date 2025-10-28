# green david app — Calendar mobile overflow fix

Tato oprava řeší „rozlézání do stran“ na mobilu u stránky **/calendar**.
Hlavní změny jsou v `app/static/css/app.css` – ovládací lišta kalendáře se nyní zalamuje,
štítek měsíce je pružný a mřížka se vejde do šířky obrazovky.

## Nasazení (GitHub -> Render)
1. V repo **green-david-app_1.1** nahraď tento soubor:  
   `app/static/css/app.css` tím z tohoto balíčku.
2. Commit + push.
3. Na Renderu udělej redeploy (nebo počkej na automat).

Hotovo – na iPhonu i Androidu se stránka nebude horizontálně posouvat.

---
Pokud chceš, můžu připravit i kompletní ZIP celé app s už aplikovanou změnou.
