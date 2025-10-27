green david app — READY FIX: redirect calendar.html → /calendar
===============================================================

Co to udělá
- Přepíše kořenový `calendar.html` na jednoduchou stránku, která **okamžitě přesměruje** na `/calendar`.
- Přidá `app/views_redirect.py` (volitelné) — server‑side redirect 301 na `/calendar`.

Proč: Statická `calendar.html` obcházela Flask šablonu a tím **mobilní CSS** — proto se layout na mobilu rozlézal.

Jak nasadit
1) Nakopíruj obsah ZIPu do kořene repa (přepiš existující `calendar.html`).
2) (Doporučeno) Registruj redirect blueprint: ve `wsgi.py` nebo tam, kde registruješ blueprinty, přidej:
   from app.views_redirect import redirects_bp
   app.register_blueprint(redirects_bp)
3) Redeploy na Renderu.

Volitelně – úklid
- Pokud chceš mít úplně čisto, můžeš později `calendar.html` **smazat** (redirect zůstane řešen na serveru přes blueprint).
- Změň v `index.html` odkaz `"/calendar.html"` na `"/calendar"` (není nutné, ale doporučeno).
- Stejný princip platí i pro případné jiné legacy stránky `*.html` v kořeni.

Ověření
- Otevření `/calendar.html` i `/calendar` skončí na stejné stránce.
- Na mobilu už **není** horizontální posuv a mřížka drží 7 sloupců v šířce viewportu.
