
# green david app — Auth bar bottom-dock (v1.0)

Tato úprava přesune informační pruh (Přihlášen: … / Odhlásit) z horní části přes logo
do decentního **dolního plovoucího pruhu**. Je to čistě CSS patch.

## Co nahradit
- Nahraďte soubor `style.css` tímto souborem **nebo** vložte následující blok na *konec* vašeho style.css.

> Pokud si nepřejete přepisovat celý soubor, stačí přidat pravidla z komentáře
> `/* === Auth bar bottom-dock patch (v1.0) === */` až na konec stávajícího `style.css`.

## Poznámky
- Selektor cílí na `.brand .right` (případně `.right.small`) – je shodný s vaším HTML.
- Na mobilu je pruh přes celou šířku (s okraji), na desktopu je ukotven vpravo dole.
- iOS safe area je zohledněná (`env(safe-area-inset-bottom)`).

