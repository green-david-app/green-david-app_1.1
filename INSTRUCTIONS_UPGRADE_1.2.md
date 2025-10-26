
# green david app – Upgrade Pack 1.2 (Kalendář + Výkazy)

Tento balíček obsahuje pouze nové/aktualizované soubory, abyste nemuseli přepisovat celý repozitář.

## Postup (bezpečný upgrade, nic nerozbít)
1) Vytvořte si branch/backup existujícího stavu (doporučeno).
2) Váš projekt otevřete vedle tohoto balíčku. Následující soubory zkopírujte/nahraďte dle stejných cest:

   - wsgi.py
   - gd/__init__.py
   - gd/db.py
   - gd/models.py
   - gd/api/__init__.py
   - gd/views/__init__.py
   - gd/views/calendar.py
   - gd/views/timesheets.py
   - templates/base.html
   - templates/calendar.html
   - templates/timesheets.html
   - static/style.css
   - requirements.txt
   - README.md

   Poznámka: `app.db` se vytváří automaticky při spuštění; pokud už ho máte, nepřepisujte ho.

3) Nechte UI a ostatní soubory, které máte v repozitáři, tak jak jsou – tento pack je nezasahuje.
4) Po instalaci balíčku proveďte:
   ```bash
   pip install -r requirements.txt
   gunicorn --workers 2 --threads 4 --timeout 120 --bind 0.0.0.0:5000 wsgi:app
   ```
5) Ověřte:
   - /calendar funguje (měsíční přehled, přidání položky)
   - /timesheets funguje (přidání záznamu, export CSV)

## Poznámky
- Pokud máte vlastní `style.css` nebo šablony, porovnejte změny diffem a případně je sloučte.
- Nepřidáváme nic, co by mazalo/zasahovalo do jiných částí projektu.
