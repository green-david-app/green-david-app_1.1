Mobile Patch v2 (2025‑10‑26)
---------------------------
Zaměřeno na:
- roztékání kalendáře doprava (ořezané „pilulky“ na kraji),
- překládání tlačítek (+ Poznámka, + Úkol, + Zakázka) přes header,
- bezpečný scroll části s kalendářem na iOS.

Nasazení
1) Nahrajte `assets/mobile-v2.css` (např. do `/static/assets/`).
2) Do `<head>` přidejte **za vaše hlavní CSS**:
   <link rel="stylesheet" href="/static/assets/mobile-v2.css">

Doporučeno (pokud můžete upravit HTML):
- Obalte grid kalendáře do `<div class="calendar-scroller"> ... </div>` pro plynulejší posouvání.