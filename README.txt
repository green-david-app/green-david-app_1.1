Instalace opravy (2 kroky):
1) Nahrajte do kořene projektu soubory: main.py, wsgi.py, requirements.txt (přepište původní).
2) Nahrajte fix-frontend.js do stejné složky jako index.html (a calendar.html) a do obou HTML
   vložte před </body> tag:
   <script src="fix-frontend.js?v=20251019"></script>
Hotovo. Není třeba nic dalšího měnit.