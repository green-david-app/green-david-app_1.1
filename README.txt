UI hotfix (ZIP) – vrací původní „tmavou“ podobu

Co je uvnitř:
- static/style.css … hlavní vzhled (záhlaví s kapslí, tmavé panely, badge, tlačítka)
- static/patch/override.css … drobné úpravy FullCalendaru
- templates/base.html … šablona s horní lištou a kartami

Jak nasadit:
1) Nahrajte obsah složky `static/` do vašeho projektu do stejné složky, kde už máte `style.css` a `patch/override.css`.
   Soubor `style.css` tím přepište (ten současný je nejspíš prázdný => proto bílý vzhled).
2) Pokud používáte Jinja šablony, ujistěte se, že CSS linkujete přes:
     <link rel="stylesheet" href="{{ url_for('static', filename='style.css') }}">
   To zajistí správnou cestu na Renderu.
3) Po deployi případně přidejte query param kvůli cache bustingu, např.:
     {{ url_for('static', filename='style.css', v='20251017a') }}
4) V logu dříve bylo vidět `style.css 200 0` (0 bajtů). Tahle ZIP sada to řeší – soubor má ~4kB.

Tip: Pokud máte vlastní base.html, stačí si z něj vzít jen CSS link a případně třídy.