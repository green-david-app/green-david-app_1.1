green david app — Mobile Overflow HOTFIX 2
=========================================

Co je v balíčku
- app/templates/base.html – přidán link na /static/assets/mobile-hotfix.css (silnější clamp)
- app/templates/calendar.html – zabaleno do .calendar-panel > .calendar-wrapper a grid je uvnitř
- static/assets/mobile-hotfix.css – pravidla, která zabrání přetečení doprava na mobilu

Nasazení
1) Nahraj soubory tak, aby nahradily stejné cesty v repozitáři.
2) Ujisti se, že už natahuješ /static/assets/mobile-lock.css (zůstává) a nově i /static/assets/mobile-hotfix.css.
3) Redeploy / restart na Renderu.

Kontrola
- iPhone/Android: na stránce /calendar se nesmí objevit horizontální scroll.
- 7 sloupců měsíce drží 100% šířky; pravý okraj se neusekává a nic nepřetéká.
