# 🚀 Navržená vylepšení pro Green David App

## ✅ JIŽ IMPLEMENTOVÁNO

### 1. Globální vyhledávání (Cmd/Ctrl+K)
- **Soubor**: `static/global-search.js`
- **Funkce**: 
  - Stiskněte `Cmd+K` (Mac) nebo `Ctrl+K` (Windows/Linux)
  - Vyhledává napříč zakázkami, úkoly, zaměstnanci
  - Rychlé výsledky s kategoriemi
  - Navigace pomocí šipek
- **Status**: ✅ Hotovo

### 2. Klávesové zkratky
- **Soubor**: `static/keyboard-shortcuts.js`
- **Funkce**:
  - `N` - Nová zakázka/úkol (podle aktuální stránky)
  - `T` - Nový úkol
  - `E` - Nový výkaz
  - `?` - Zobrazit všechny zkratky
  - `Esc` - Zavřít modaly
- **Status**: ✅ Hotovo

### 3. Toast notifikace
- **Soubor**: `static/toast.js`
- **Funkce**: Success, Error, Warning, Info notifikace
- **Status**: ✅ Hotovo

### 4. Loading states
- **Soubor**: `static/loading.js`
- **Funkce**: Loading overlay pro async operace
- **Status**: ✅ Hotovo

---

## 💡 DOPORUČENÁ VYLEPŠENÍ (Prioritizováno)

### 🔥 VYSOKÁ PRIORITA

#### 1. **Bulk Operations (Hromadné operace)**
**Proč**: Ušetří čas při práci s více položkami
**Implementace**:
- Checkboxy u každé karty (zakázky, úkoly)
- Toolbar s akcemi: Smazat, Změnit status, Přiřadit zaměstnance
- Select All / Deselect All

**Kde**: `jobs.html`, `tasks.html`

#### 2. **Deadline Notifications (Upozornění na deadline)**
**Proč**: Předejde zmeškaným termínům
**Implementace**:
- Badge s počtem urgentních úkolů v headeru
- Toast notifikace při blížícím se deadline
- Automatické upozornění (např. 3 dny před)

**Kde**: Globální komponenta

#### 3. **Dark/Light Mode Toggle**
**Proč**: Lepší UX, možnost přepínání témat
**Implementace**:
- Toggle v headeru (🌙/☀️)
- Uložení preference do localStorage
- Smooth transition
- Aplikace na všechny stránky

**Kde**: `app-settings.js`, header všech stránek

---

### ⚡ STŘEDNÍ PRIORITA

#### 4. **Quick Actions FAB (Floating Action Button)**
**Proč**: Rychlý přístup k nejčastějším akcím
**Implementace**:
- FAB v pravém dolním rohu
- Kontextové menu podle aktuální stránky
- Animace při hover

**Kde**: Globální komponenta

#### 5. **Export/Import dat**
**Proč**: Záloha dat, migrace, reporting
**Implementace**:
- Export do PDF (jsPDF)
- Export do Excel (SheetJS)
- Export do CSV
- Import z CSV s validací

**Kde**: Nový soubor `static/export-import.js`

#### 6. **Drag & Drop pro úkoly**
**Proč**: Intuitivní změna statusu
**Implementace**:
- Drag & drop mezi sloupci (K dokončení → Probíhá → Hotovo)
- Vizuální feedback
- Auto-save

**Kde**: `tasks.html` (rozšířit stávající)

---

### 📊 NÍZKÁ PRIORITA (Nice to have)

#### 7. **Dashboard Widgets Customization**
**Proč**: Personalizace podle potřeb uživatele
**Implementace**:
- Drag & drop widgetů
- Přidat/odebrat widgety
- Uložení layoutu

**Kde**: `index.html` Dashboard

#### 8. **Offline Support (Service Worker)**
**Proč**: Práce bez internetu
**Implementace**:
- Service Worker pro cache
- Offline indicator
- Sync při obnovení připojení

**Kde**: Nový soubor `service-worker.js`

#### 9. **Komentáře k zakázkám/úkolům**
**Prož**: Lepší komunikace v týmu
**Implementace**:
- Komentáře v detailu zakázky/úkolu
- @mention zaměstnanců
- Notifikace při novém komentáři

**Kde**: Rozšířit modaly v `jobs.html`, `tasks.html`

#### 10. **Přílohy k úkolům**
**Proč**: Sdílení souborů
**Implementace**:
- Upload souborů
- Zobrazení příloh
- Download

**Kde**: Rozšířit modaly v `tasks.html`

---

## 🎯 DOPORUČENÝ PLÁN IMPLEMENTACE

### Fáze 1 (1-2 dny)
1. ✅ Globální vyhledávání
2. ✅ Klávesové zkratky
3. Dark/Light mode toggle
4. Deadline notifications

### Fáze 2 (2-3 dny)
5. Bulk operations
6. Quick Actions FAB
7. Drag & Drop pro úkoly

### Fáze 3 (3-4 dny)
8. Export/Import dat
9. Komentáře
10. Přílohy

### Fáze 4 (volitelné)
11. Dashboard customization
12. Offline support

---

## 📝 TECHNICKÉ POZNÁMKY

### Pro implementaci Dark/Light mode:
```javascript
// V app-settings.js
function toggleTheme() {
    const current = localStorage.getItem('theme') || 'dark';
    const newTheme = current === 'dark' ? 'light' : 'dark';
    localStorage.setItem('theme', newTheme);
    document.documentElement.setAttribute('data-theme', newTheme);
    applyTheme(newTheme);
}
```

### Pro Bulk Operations:
```javascript
// V jobs.html nebo tasks.html
let selectedItems = new Set();

function toggleSelection(id) {
    if (selectedItems.has(id)) {
        selectedItems.delete(id);
    } else {
        selectedItems.add(id);
    }
    updateBulkToolbar();
}

function bulkDelete() {
    if (confirm(`Smazat ${selectedItems.size} položek?`)) {
        selectedItems.forEach(id => deleteItem(id));
        selectedItems.clear();
    }
}
```

### Pro Export do PDF:
```javascript
// Použít jsPDF
import jsPDF from 'jspdf';

function exportToPDF(data) {
    const doc = new jsPDF();
    // ... generování PDF
    doc.save('export.pdf');
}
```

---

## 🎨 UX VYLEPŠENÍ

1. **Smooth transitions** - Všechny animace by měly být plynulé (0.2-0.3s)
2. **Loading states** - Vždy zobrazit loading při async operacích
3. **Error handling** - Uživatelsky přívětivé chybové zprávy
4. **Empty states** - Pěkné zobrazení prázdných stavů
5. **Tooltips** - Pomocné texty u ikon a tlačítek
6. **Confirmation dialogs** - Pro destruktivní akce (smazat, atd.)

---

## 🔒 BEZPEČNOST

1. **XSS Protection** - Vždy používat `escapeHtml()` pro user input
2. **CSRF Protection** - Pro API calls
3. **Input Validation** - Validovat všechna vstupní data
4. **Rate Limiting** - Omezit počet requestů

---

## 📱 MOBILNÍ OPTIMALIZACE

1. **Touch gestures** - Swipe pro smazání, atd.
2. **Responsive design** - Všechny komponenty musí fungovat na mobilu
3. **Mobile menu** - Hamburger menu pro navigaci
4. **Touch targets** - Minimálně 44x44px pro tlačítka

---

## 🚀 PERFORMANCE

1. **Lazy loading** - Načítat data až když je potřeba
2. **Debouncing** - Pro search inputy
3. **Virtual scrolling** - Pro dlouhé seznamy
4. **Image optimization** - Komprese obrázků

---

**Poslední aktualizace**: 2026-01-15
**Status**: Vylepšení 1-2 implementováno ✅

