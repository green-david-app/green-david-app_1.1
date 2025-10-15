
green david — UI polish patch (2025‑10‑15)
=========================================

Co je uvnitř
------------
- static/css/app.css            → přepracované styly (mobilní kalendář, spacing, kontrast)
- static/js/mobile-fixes.js     → drobná JS „pojistka“ (skryje textový banner „Přihlášený uživatel…“ na mobilu a položku „Admin“)

Jak nasadit (bez úprav šablon)
------------------------------
1) Nahraďte *static/css/app.css* tímto souborem.
2) Ujistěte se, že se načítá *static/js/mobile-fixes.js*. Pokud už máte globální `base.html` / `layout.html`,
   přidejte TAG před koncem `<body>`:

   `<script src="{{ url_for('static', filename='js/mobile-fixes.js') }}"></script>`

   (Pokud už skript načítáte jinde, tento krok přeskočte.)

Poznámky
--------
- Odkaz „Admin“ je na mobilech automaticky skrytý (zůstává na tabletu/desktopu).
- Kalendář má konzistentní mřížku, menší rádiusy, čitelnější štítky úkolů a lepší odsazení.
- Spodní hláška „Přihlášený uživatel neznámý“ se na mobilu schová, aby nepřekážela.
- Stylování je defenzivní: selektory cílí na elementy obsahující „calendar/day/event“ v názvu třídy/id.

Render
------
Po nahrání změn stačí standardní redeploy. Start command beze změny:
`gunicorn --workers 2 --threads 4 --timeout 120 --bind 0.0.0.0:$PORT wsgi:app`
