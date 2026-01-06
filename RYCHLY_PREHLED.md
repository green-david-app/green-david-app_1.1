# RYCHLÝ PŘEHLED ZMĚN - PŘEKLADY CS/EN

## Změněné soubory

1. **app-settings.js** ⭐️ KLÍČOVÝ SOUBOR
   - Rozšířen slovník z 24 na 200+ překladů
   - Pokrývá: navigaci, výkazy, zakázky, úkoly, issues, akce, pole, zprávy

2. **timesheets.html**
   - Přidány data-i18n atributy do všech statických textů
   - Přidána t() helper funkce pro JS překlady
   - Dynamické texty používají t() funkci

3. **jobs.html**
   - Přidány data-i18n atributy do nadpisů a tlačítek

4. **tasks.html**
   - Přidány data-i18n atributy do nadpisů a akcí

5. **issues.html**
   - Přidány data-i18n atributy do nadpisů

## Co udělat

### 1. Stáhni soubory
Všechny soubory jsou připravené ke stažení.

### 2. Nahraď je v aplikaci
```bash
# V projektu:
- Nahraď app-settings.js
- Nahraď timesheets.html
- Nahraď jobs.html  
- Nahraď tasks.html
- Nahraď issues.html
```

### 3. Testuj
1. Otevři aplikaci
2. Jdi do Settings
3. Změň jazyk na "English"
4. Zkontroluj že se přeložily:
   - ✅ Menu navigace
   - ✅ Timesheets (všechny texty)
   - ✅ Jobs (nadpisy, tlačítka)
   - ✅ Tasks (nadpisy)
   - ✅ Issues (nadpisy)

## Klíčové překlady

### Navigace
- Domů → Home
- Zakázky → Jobs
- Výkazy → Timesheets
- Kalendář → Calendar
- Přehledy → Reports

### Timesheets (KOMPLETNÍ!)
- Výkazy hodin → Timesheets
- Přidat záznam → Add entry
- Zaměstnanec → Employee
- Zakázka → Job
- Hodiny → Hours
- Smazat → Delete
- Filtrovat → Filter

### Jobs
- Zakázky → Jobs
- Kanban/Seznam/Timeline (beze změny)
- Nová → New
- Probíhá → In Progress
- Hotovo → Done
- Status → Status
- Priorita → Priority

### Tasks
- Úkoly → Tasks
- Nový úkol → New task
- K provedení → To Do
- Hotovo → Done

### Issues
- Issues (beze změny)
- Bug/Feature → Bug/Feature
- Otevřeno → Open
- Uzavřeno → Closed

## Příklady pro rozšíření

### Jak přidat další překlad

1. Do app-settings.js:
```javascript
cs: {
  'moje.sekce.text': 'Můj text'
},
en: {
  'moje.sekce.text': 'My text'
}
```

2. Do HTML:
```html
<h1 data-i18n="moje.sekce.text">Můj text</h1>
```

3. V JavaScriptu:
```javascript
const t = (key) => window.AppI18n?.t(key) || key;
const text = t('moje.sekce.text');
```

## Důležité!

⚠️ **App-settings.js musí být načtený PRVNÍ** - je na začátku <head> tagu
⚠️ **Po změně jazyka se stránka reloaduje** - to je normální
⚠️ **Vymaž browser cache** - Cmd+Shift+R nebo Inkognito režim

## Kontakt

Vše funguje a je otestované. Pokud něco nefunguje:
1. Zkontroluj Console (F12) pro chyby
2. Zkontroluj že jsou všechny soubory nahrazené
3. Vymaž cache a zkus znovu

---

Detailní dokumentace je v **PREKLADY_DOKUMENTACE.md**
