green david app · MOBILE PACK (compact calendar, responsive, footer, export)

Integrované:
- Kompaktní kalendář (menší písmo/odsazení při ≥2 položkách) + modal s detailem.
- Lepící footer dole s informací o přihlášeném (čte /api/me).
- Výkazy: filtry, opravené ukládání, export CSV/XLSX.
- Všechny stránky už mají vložený <script src="/common-footer.js" defer></script>.

Nasazení:
1) Nahraj soubory do kořene a přepiš existující (calendar.html, timesheets.html, mobile-override.css, common-footer.js).
2) Hard refresh prohlížeče (na iOS dlouze podrž ↻ → Reload).

Změna hranice „kompakt“:
- V `calendar.html` uprav: `if (todays.length >= 2) cell.classList.add('compact');` (např. na 3).

Pozn.: Styl je navržen pro tmavé barvy appky; přebarvení řeší /style.css.
