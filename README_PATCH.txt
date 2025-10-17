green-david-app patch – 2025-10-17 (v20251017a)

Instalace:
1) Nahraj složku /static/patch/ do aplikace.
2) V calendar.html používej:
   <link rel="stylesheet" href="/static/patch/override.css?v=20251017a">
   <script src="/static/patch/calendar-patch.js?v=20251017a" defer></script>
3) Pro jistotu obnov stránku naplno (Ctrl+F5).

Co se opravuje:
- DELETE požadavky vždy s credentials: 'include' (funguje s přihlášením).
- Mazání starých i nových záznamů: více kompatibilních endpointů (DELETE /api/jobs/<id>, DELETE /api/jobs?id=, DELETE s JSON body, POST /api/jobs/delete).
- Při 409 (navázané záznamy) zobrazí jasnou zprávu + stále odstraní samotný zápis v kalendáři.
- Po úspěchu se kalendář automaticky obnoví.
