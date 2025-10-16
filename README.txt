GDA hotfix 2025-10-16

Soubory zkopírujte do stejné struktury na serveru:

  /static/patch/override.css
  /mobile-override.css
  /static/patch/calendar-patch.js

A v souboru calendar.html (na konci stránky) měj jen tento řádek:
  <script src="/static/patch/calendar-patch.js" defer></script>

Pak tvrdě obnov prohlížeč (Cmd+Shift+R / potáhnout dolů na iOS).
