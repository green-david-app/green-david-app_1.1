# OPRAVA PŘEPÍNÁNÍ JAZYKA A DARK/LIGHT MODE

## Co bylo opraveno

### 1. settings.js
**Problém:** Syntax error na řádku 655 - neočekávané klíčové slovo 'catch'
**Příčina:** Duplicitní a neúplný kód ve funkci `exportData()` - obsahoval uzavření funkce (`};`) a následně zbytek staré verze s try-catch blokem bez try části.

**Oprava:**
- Odstraněn duplicitní kód z řádků 637-658
- Funkce `exportData()` nyní správně končí na řádku 636
- Odstraněna chybná reference na neexistující funkci `formatDate()` a nahrazena za `toLocaleString('cs-CZ')`

### 2. app-settings.js  
**Problém:** Chybějící funkce `saveAppSettings()` která byla volána na řádku 117
**Příčina:** Funkce nebyla nikdy definována, ale byla používána v `window.AppI18n.setLanguage()`

**Oprava:**
- Přidána funkce `saveAppSettings(settings)` za funkci `loadAppSettings()` na řádcích 154-159
- Funkce správně ukládá nastavení do localStorage s error handlingem

## Co nyní funguje

### Přepínání jazyka (CS/EN)
- Select `#userLanguage` v settings.html správně detekuje změnu
- Jazyk se ukládá do `localStorage.appSettings.userLanguage`
- `window.AppI18n.setLanguage()` aplikuje překlady na elementy s `data-i18n` atributem
- Stránka se automaticky reloaduje pro aplikování změn všude

### Dark/Light mode
- Checkbox `#darkModeToggle` správně přepína mezi 'dark' a 'light'
- Téma se ukládá do `localStorage.appSettings.theme`
- `data-theme` atribut na `<html>` elementu se správně nastavuje
- CSS proměnné v `static/style.css` reagují na změnu `[data-theme="dark"]` a `[data-theme="light"]`

## Jak otestovat

1. **Jednoduchý test:**
   - Otevři `test-settings.html` v prohlížeči
   - Zkus přepnout mezi Dark/Light mode
   - Zkus změnit jazyk z CS na EN a zpět
   - Klikni na "Test uložení nastavení" - měly by se zobrazit aktuální hodnoty

2. **V aplikaci:**
   - Otevři Settings (/settings.html)
   - Přepni Dark mode toggle - stránka by se měla okamžitě změnit
   - Změň jazyk v selectu - stránka se reloadne a texty s `data-i18n` atributem se přeloží
   - Zkontroluj v Developer Console (F12) → Application → Local Storage → appSettings

## Poznámky

- Všechny změny jsou **backwards compatible** - existující nastavení v localStorage zůstanou zachována
- Jazyk funguje pouze pro elementy které mají atribut `data-i18n`
- V aplikaci je zatím omezený počet přeložených textů - je třeba přidat více překladů do `I18N_DICT` v `app-settings.js`
- Dark/Light mode funguje globálně díky CSS proměnným v `static/style.css`

## Co by se mělo ještě dodělat

1. Přidat více překladů do `I18N_DICT` v `app-settings.js`
2. Přidat `data-i18n` atributy na více elementů v HTML šablonách
3. Případně přidat překlady pro placeholdery pomocí `data-i18n-placeholder`
4. Otestovat na všech stránkách aplikace
5. Možná přidat persistenci jazyka bez reloadu stránky (složitější, ale možné)

## Soubory ke stažení

- `settings.js` - opravený hlavní settings script
- `app-settings.js` - opravený globální settings script
- `test-settings.html` - testovací stránka pro rychlé ověření funkčnosti

## Instalace oprav

1. Zálohuj si současné soubory:
   ```bash
   cp settings.js settings.js.backup
   cp app-settings.js app-settings.js.backup
   ```

2. Nahraď soubory opravenými verzemi

3. Pokud běží aplikace lokálně, restartuj ji nebo stiskni Ctrl+C a znovu spusť

4. Vymaž browser cache nebo otevři stránku v režimu Inkognito pro testování

## Jak to funguje technicky

### Flow při změně jazyka:
1. User změní select `#userLanguage`
2. Event listener v `settings.js` (řádek 383) zachytí změnu
3. Uloží se `currentSettings.userLanguage = e.target.value`
4. Zavolá se `saveSettings()` → uloží do localStorage
5. Zavolá se `window.AppI18n.setLanguage()` → aplikuje překlady
6. `window.location.reload()` → reloadne stránku
7. Při načtení stránky `app-settings.js` automaticky aplikuje uložený jazyk

### Flow při změně tématu:
1. User přepne checkbox `#darkModeToggle`
2. Event listener v `settings.js` (řádek 266) zachytí změnu
3. Uloží se `currentSettings.theme = 'dark' nebo 'light'`
4. Zavolá se `saveSettings()` → uloží do localStorage
5. Zavolá se `applyTheme()` → nastaví `data-theme` atribut a inline styly
6. CSS automaticky reaguje na změnu `[data-theme]` selectoru
