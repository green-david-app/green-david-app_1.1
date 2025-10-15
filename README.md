# green david – Mobile hot‑fix (Kalendář)

**Co opravuje:**
- Kalendář se dá **scrollovat** (uvnitř obrazovky, i na iOS).
- Dny se **přeskupí podle šířky** (1 sloupec → 2 → 3 → 7 na širokých displejích).
- **Kliknutí na záznam** funguje přes `data-href` nebo vnitřní `<a>`.
- Zabraňuje, aby **neviditelný overlay** „sežral“ tapy.

## Instalace
1) Do `<head>` **za** vaše CSS přidejte:
```html
<link rel="stylesheet" href="/static/patch/override.css">
```
2) Před `</body>` přidejte:
```html
<script src="/static/patch/calendar-patch.js"></script>
```

## Minimální markup
Kontejner s dny ideálně označte:
```html
<div data-calendar-grid> … denní buňky … </div>
```
Záznamy (badge) udělejte klikací přes `data-href`:
```html
<div class="gd-event" data-href="/gd/jobs/123">…</div>
```
Nemáte-li `data-href`, patch vezme první `<a href>` uvnitř.

## Poznámky
- Jestli máte fixní header/tabbar, výšku dolaďte v `.gd-calendar-wrap` (výchozí odečet ~140px).
- Pokud už používáte vlastní overlaye, ponechte jim `pointer-events:auto` pouze když jsou viditelné.
