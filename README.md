# Universal Mobile Patch (green david app)

Drop‑in sada pro "univerzální" chování na telefonech různých velikostí – beze změny vizuálního stylu.

## Co je uvnitř
- `mobile-universal.css` – bezpečné fluidní typy, bezpečné zóny (notch), utility pro sticky prvky, tabulky jako karty, základní minimální tap velikosti.
- `mobile-universal.js` – korektní výška 100vh na mobilech, doplnění `viewport-fit=cover`, pomoc při posunu formulářů nad klávesnici.

## Jak nasadit (bez zásahů do existujícího UI)
1. Přidejte do `<head>` **za** existující CSS:
   ```html
   <link rel="stylesheet" href="/static/css/mobile-universal.css">
   ```
2. Přidejte do konce `<body>`:
   ```html
   <script src="/static/js/mobile-universal.js"></script>
   ```
3. (Volitelné) Obalte široké tabulky:
   ```html
   <div class="table-responsive">
     <table>…</table>
   </div>
   ```
   Nebo pro zobrazení „karty“ na extra úzkých telefonech přidejte nad tabulku třídu `as-cards` a do `<td>` doplňte `data-label="Název sloupce"`.

4. (Volitelné) Kalendářní gridu přidejte třídu `gd-calendar`, která automaticky přizpůsobí velikost dnů.
5. (Volitelné) Na lepší mobile UX použijte utility třídy: `u-stack`, `u-wrap`, `u-scroll`, `sticky-top`, `sticky-bottom`.

## Poznámky
- Písmo ve formulářích je >= 16px, takže iOS nezvětšuje při fokusu celou stránku.
- Výška obrazovky na mobilech: v CSS můžete použít `height: calc(var(--vh) * 100);` např. pro plnoobrazovkové panely.
- Patch je „additive“: nepřepisuje vaše barvy ani layouty, jen přidává mobilní jističe.
