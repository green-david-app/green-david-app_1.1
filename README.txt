Export: Globální vyhledávání + jednotné záložky (green-david app)

Co je uvnitř
- templates/layout.html  – doplněné linky na CSS, skript pro globální vyhledávání a injektor záložek.
- templates/brigadnici.html – vyčištěno: odstraněné lokální záložky a inline vyhledávání; využívá globální.

Co už v repu JE a nic do něj nevkládej (jen musí být k dispozici na URL):
- /static/js/gd_global_search_card.js
- /static/css/gd_enhancements.css
- /static/css/gd_global_search_card.css

Jak nasadit (jen přepsat existující soubory těmito):
1) Nahraj templates/layout.html (přepíše starý „layout“)
2) Nahraj templates/brigadnici.html (bez lokálních tabs a inline search)
