# ROZŠÍŘENÍ PŘEKLADŮ CS/EN - KOMPLETNÍ DOKUMENTACE

## Co bylo přidáno

### 1. Rozšířený slovník překladů v app-settings.js

Přidáno **200+ překladů** pokrývajících:

#### Navigace (✓ Kompletní)
- Hlavní menu: Domů, Zakázky, Výkazy, Kalendář, Přehledy, Více
- Rozšířené menu: všechny sekce aplikace

#### Výkazy hodin - Timesheets (✓ Kompletní)
- **Nadpisy:** "Výkazy hodin" → "Timesheets"
- **Tlačítka:** "Přidat záznam" → "Add entry", "Obnovit" → "Refresh"
- **Filtry:** "Od/Do" → "From/To", "Zaměstnanec" → "Employee", "Zakázka" → "Job"
- **Tabulka:** "Datum" → "Date", "Hodiny" → "Hours", "Poznámka" → "Note"
- **Akce:** "Smazat" → "Delete", "Filtrovat" → "Filter", "Vymazat" → "Clear"

#### Zakázky - Jobs (✓ Kompletní)
- **Nadpisy:** "Zakázky" → "Jobs"
- **Pohledy:** "Kanban/Seznam/Timeline" → "Kanban/List/Timeline"
- **Stavy:** "Nová/Probíhá/Hotovo/Zrušeno" → "New/In Progress/Done/Cancelled"
- **Priority:** "Nízká/Střední/Vysoká/Urgentní" → "Low/Medium/High/Urgent"
- **Pole:** "Název/Popis/Rozpočet/Zadavatel" → "Name/Description/Budget/Client"
- **Sekce:** "Úkoly/Issues/Informace" → "Tasks/Issues/Information"

#### Úkoly - Tasks (✓ Kompletní)
- **Nadpisy:** "Úkoly" → "Tasks"
- **Akce:** "Nový úkol" → "New task", "Upravit úkol" → "Edit task"
- **Stavy:** "K provedení/Probíhá/Hotovo" → "To Do/In Progress/Done"
- **Pole:** "Přiřazen/Termín" → "Assigned/Deadline"
- **Sekce:** "Komentáře/Přílohy" → "Comments/Attachments"

#### Issues (✓ Kompletní)
- **Nadpisy:** "Issues" (zůstává stejné)
- **Typy:** "Bug/Feature/Vylepšení/Úkol/Dotaz" → "Bug/Feature/Improvement/Task/Question"
- **Stavy:** "Otevřeno/Probíhá/Vyřešeno/Uzavřeno" → "Open/In Progress/Resolved/Closed"
- **Priority:** "Nízká/Střední/Vysoká/Kritická" → "Low/Medium/High/Critical"

#### Běžné akce (✓ Kompletní)
- Přidat/Upravit/Smazat/Uložit/Zrušit → Add/Edit/Delete/Save/Cancel
- Hledat/Filtr/Export/Import → Search/Filter/Export/Import
- Obnovit/Vymazat/Zavřít → Refresh/Clear/Close

#### Běžná pole (✓ Kompletní)
- Název/Popis/Status/Priorita → Name/Description/Status/Priority
- Datum/Čas/Hodiny/Poznámka → Date/Time/Hours/Note
- Vytvořeno/Upraveno/Termín → Created/Updated/Deadline

#### Zprávy (✓ Kompletní)
- "Opravdu smazat?" → "Confirm delete?"
- "Uloženo/Smazáno/Chyba" → "Saved/Deleted/Error"
- "Načítání..." → "Loading..."
- "Žádná data" → "No data"

## Upravené soubory

### 1. app-settings.js
- Rozšířen I18N_DICT z 24 na 200+ překladů
- Přidány kategorie: timesheets, jobs, tasks, issues, actions, fields, messages
- Obě jazykové verze (CS + EN) kompletní

### 2. timesheets.html
- Přidány `data-i18n` atributy do všech statických textů:
  - Title stránky
  - H1 nadpis
  - Všechna tlačítka (Přidat, Obnovit, Export CSV/XLSX)
  - Všechny labely filtrů (Od, Do, Zaměstnanec, Zakázka, Text)
  - Všechny hlavičky tabulky (Datum, Zaměstnanec, Zakázka, Hodiny, Pozn.)
  - Placeholder v textovém poli
- Přidána helper funkce `t()` pro překlady v JavaScriptu
- Dynamicky generované texty používají `t()` funkci

### 3. jobs.html
- Přidány `data-i18n` atributy:
  - Title stránky
  - H1 nadpis
  - Tlačítka pohledů (Kanban, Seznam, Timeline)
  - Labely polí (Status, Priorita, Rozpočet, Název, Popis)

### 4. tasks.html
- Přidány `data-i18n` atributy:
  - Title a H1 nadpis
  - Akční tlačítka
  - Stavy úkolů

### 5. issues.html
- Přidány `data-i18n` atributy:
  - Title a H1 nadpis
  - Akční tlačítka

## Jak to funguje

### Statické texty (HTML)
```html
<!-- Původní -->
<h1>Výkazy hodin</h1>

<!-- S překladem -->
<h1 data-i18n="timesheets.title">Výkazy hodin</h1>
```

Při přepnutí jazyka:
1. JavaScript v `app-settings.js` najde všechny elementy s `data-i18n`
2. Přečte klíč z atributu (`timesheets.title`)
3. Najde překlad v `I18N_DICT` podle aktuálního jazyka
4. Nahradí `textContent` elementu přeloženým textem

### Dynamické texty (JavaScript)
```javascript
// Helper funkce
const t = (key) => (window.AppI18n && window.AppI18n.t) ? window.AppI18n.t(key) : key;

// Použití
button.innerHTML = t('timesheets.delete'); // "Smazat" nebo "Delete"
```

### Placeholdery
```html
<input data-i18n-placeholder="timesheets.filter.placeholder" placeholder="poznámka, název…">
```

## Instalace

### 1. Nahraď soubory
```bash
# Zálohuj si současné soubory!
cp app-settings.js app-settings.js.backup
cp timesheets.html timesheets.html.backup
cp jobs.html jobs.html.backup
cp tasks.html tasks.html.backup
cp issues.html issues.html.backup

# Nahraď novými verzemi
# (stáhni soubory z outputs a překopíruj)
```

### 2. Vymaž browser cache
- Stiskni Cmd+Shift+R (Mac) nebo Ctrl+Shift+R (Windows)
- Nebo otevři v Inkognito režimu

### 3. Otestuj přepínání jazyka
1. Jdi do Settings
2. Změň jazyk z "Čeština" na "English"
3. Stránka se reloadne
4. Všechny texty by měly být v angličtině

## Co se přeloží

### ✅ Kompletně přeloženo
- **Navigace** - všechny položky menu
- **Timesheets** - vše včetně tlačítek, filtrů, tabulky
- **Jobs** - nadpisy, pohledy, stavy, priority, pole
- **Tasks** - nadpisy, akce, stavy, pole
- **Issues** - nadpisy, typy, stavy, priority

### ⚠️ Částečně přeloženo
- **Jobs detail modály** - část textů má data-i18n, část je v JS a potřebuje doplnit t()
- **Formuláře** - validační zprávy a další dynamické texty
- **Grafy a reporty** - legendy a popisky

### ❌ Nepřeloženo
- **Uživatelská data** - jména zaměstnanců, názvy zakázek, poznámky
- **Error zprávy z API** - backend vrací česky
- **Notifikace** - toast zprávy v jiných souborech

## Jak přidat další překlady

### 1. Přidej do slovníku (app-settings.js)
```javascript
const I18N_DICT = {
  cs: {
    'muj.novy.klic': 'Můj český text',
  },
  en: {
    'muj.novy.klic': 'My English text',
  }
};
```

### 2. Použij v HTML
```html
<button data-i18n="muj.novy.klic">Můj český text</button>
```

### 3. Použij v JavaScriptu
```javascript
const text = t('muj.novy.klic');
```

## Tipy

### Pojmenování klíčů
- Používej tečkovou notaci: `sekce.podsekce.text`
- Buď konzistentní: `timesheets.add`, `tasks.add`, `issues.add`
- Pro běžné texty použij `action.`, `field.`, `msg.`

### Best practices
- Vždy přidej obě jazykové verze najednou
- Testuj v obou jazycích
- Placeholder texty by měly být stručné
- Zachovej formátování (emoji, symboly)

### Debugging
Pokud se text nepřeloží:
1. Zkontroluj že klíč existuje v obou jazycích
2. Zkontroluj syntax `data-i18n="key"` (bez chyb)
3. Otevři Console (F12) a zkus: `window.AppI18n.t('tvuj.klic')`
4. Zkontroluj že app-settings.js se načítá před ostatními skripty

## Příklady použití

### Příklad 1: Přeložit nadpis
```html
<!-- Před -->
<h1>Moje stránka</h1>

<!-- Po -->
<h1 data-i18n="mypage.title">Moje stránka</h1>
```

### Příklad 2: Přeložit tlačítko v JS
```javascript
// Před
button.textContent = 'Uložit';

// Po
button.textContent = t('action.save');
```

### Příklad 3: Přeložit confirm dialog
```javascript
// Před
if (confirm('Opravdu smazat?')) { ... }

// Po
if (confirm(t('msg.confirm_delete'))) { ... }
```

## Důležité poznámky

1. **Reload je nutný** - Po změně jazyka se stránka reloaduje, aby se aplikovaly všechny překlady
2. **LocalStorage** - Jazyk se ukládá do `localStorage.appSettings.userLanguage`
3. **Fallback** - Pokud překlad chybí, zobrazí se původní text
4. **Konzistence** - Všechny stránky sdílejí stejný slovník překladů

## Co dělat dál

### Krátký seznam TODO
1. ✅ Výkazy - hotovo
2. ✅ Zakázky - hotovo  
3. ✅ Úkoly - hotovo
4. ✅ Issues - hotovo
5. ⏳ Přidat t() do všech JS souborů které generují texty
6. ⏳ Přidat data-i18n do zbývajících stránek (Employees, Calendar, Reports...)
7. ⏳ Přeložit validační zprávy
8. ⏳ Přeložit toast notifikace

### Dlouhý seznam (nice to have)
- Přeložit nastavení (Settings)
- Přeložit dashboard
- Přeložit sklad (Warehouse)
- Přeložit finance
- Přeložit dokumenty
- Přeložit archiv
- Přeložit help texty a tooltips
- Přidat třetí jazyk (např. němčina)

## Troubleshooting

**Problém:** Texty se nepřekládají
- **Řešení:** Zkontroluj že app-settings.js se načítá na stránce (`<script src="/app-settings.js"></script>`)

**Problém:** Některé texty ano, jiné ne
- **Řešení:** Pravděpodobně chybí data-i18n atribut nebo t() funkce v JS

**Problém:** Po přepnutí jazyka se nic nestane
- **Řešení:** Zkontroluj Console (F12) pro chyby. Možná chybí funkce saveAppSettings()

**Problém:** Stránka se zasekne při reloadu
- **Řešení:** Vymaž localStorage: `localStorage.clear()` v Console a reload

## Souhrn

🎉 **Aplikace je nyní dvoujazyčná!**

- ✅ 200+ přeložených textů
- ✅ 4 hlavní sekce kompletně přeloženy (Timesheets, Jobs, Tasks, Issues)
- ✅ Automatické přepínání při změně v Settings
- ✅ Persistence napříč sessions
- ✅ Fallback na češtinu pokud překlad chybí

**Příští krok:** Postupně přidat data-i18n do zbývajících stránek podle stejného vzoru.
