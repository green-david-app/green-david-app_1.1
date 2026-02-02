# Kompaktní Mobile Header + FIELD/FULL Toggle - Implementace

## ✅ DOKONČENO

### 1. Audit současného stavu
- [x] Nalezen header v `layout_mobile_field.html` a `layout_mobile_full.html`
- [x] Mode toggle existuje, ale není dostatečně viditelný
- [x] Chybí notifikace a hamburger menu
- [x] Header není optimalizován pro 320px šířku

### 2. Nový kompaktní header
- [x] **HTML struktura** - 3 zóny (logo, center, actions)
- [x] **FIELD/FULL toggle** - viditelné tlačítko s ikonami
- [x] **Notifikace** - badge s počtem nepřečtených
- [x] **Hamburger menu** - dropdown s user info a menu items

### 3. CSS styly
- [x] **Vytvořen**: `static/css/mobile-header.css`
- [x] **Optimalizace**: Vejde se na 320px šířku
- [x] **Responsive**: Podpora pro velmi malé telefony (< 360px)
- [x] **Safe area**: Podpora pro iOS notch
- [x] **Animace**: Mode toggle pulse animace

### 4. JavaScript
- [x] **Vytvořen**: `static/js/header.js`
- [x] **Dropdown menu**: Otevření/zavření, kliknutí mimo, Escape
- [x] **Mode toggle**: Přepínání FIELD/FULL s toast notifikací
- [x] **Legacy support**: Podpora pro starou funkci `toggleMode()`

### 5. Backend úpravy
- [x] **Context processor**: Přidán `user` a `unread_count` do `inject_permissions()`
- [x] **API endpoint**: `/api/user/settings` už existuje pro mode switch

## 📋 Změněné soubory

### Nové soubory:
1. `static/css/mobile-header.css` - Kompaktní header styly
2. `static/js/header.js` - Dropdown menu + mode toggle logika
3. `MOBILE_HEADER_IMPLEMENTATION.md` - Tento dokument

### Upravené soubory:
1. `templates/layouts/layout_mobile_field.html` - Nový header HTML
2. `templates/layouts/layout_mobile_full.html` - Nový header HTML
3. `static/css/mobile_field.css` - Odstraněny duplicitní header styly
4. `static/css/mobile_full.css` - Odstraněny duplicitní header styly
5. `app/utils/permissions.py` - Přidán `user` a `unread_count` do context processoru

## 🎨 Struktura headeru

```
┌─────────────────────────────────────────────────┐
│ [Logo]    Green David    [⚡] [🔔] [☰]         │
└─────────────────────────────────────────────────┘
   LEFT        CENTER       RIGHT (mode, notif, menu)
```

### LEFT ZONE:
- Logo (28x28px)
- Kliknutelné → přejde na hlavní stránku

### CENTER ZONE:
- FIELD mode: Aktuální zakázka nebo "Green David"
- FULL mode: "Green David" nebo custom title
- Skryje se na < 360px šířce

### RIGHT ZONE:
- **Mode Toggle** (⚡): Přepíná FIELD ↔ FULL
  - FIELD mode: Zobrazuje grid ikonu (pro přepnutí na FULL)
  - FULL mode: Zobrazuje home ikonu (pro přepnutí na FIELD)
- **Notifications** (🔔): Badge s počtem nepřečtených
- **Menu** (☰): Dropdown s user info a menu items

## 📱 Responsive breakpoints

### 320px - 359px (velmi malé telefony):
- Header výška: 48px
- Button velikost: 36x36px
- Center zone: Skryta
- Gap mezi buttony: 2px

### 360px+ (běžné mobily):
- Header výška: 52px
- Button velikost: 40x40px
- Center zone: Viditelná
- Gap mezi buttony: 4px

### Landscape mode:
- Header výška: 44px
- Dropdown: Max výška s scroll

### iOS notch (iPhone X+):
- Safe area padding-top
- Dropdown offset pro notch

## 🔧 Funkčnost

### Dropdown Menu:
- Otevření: Klik na hamburger menu
- Zavření: Klik mimo, Escape, scroll, resize
- Obsahuje:
  - User info (avatar, jméno, role)
  - Mode info (aktuální režim)
  - Menu items (Upravit widgety, Synchronizace, Odhlásit se)

### Mode Toggle:
- Klik na ikonu → přepne režim
- Uloží do DB (`/api/user/settings`)
- Cookie backup pro offline
- Toast notifikace
- Reload stránky po 500ms

### Notifications:
- Badge zobrazuje počet nepřečtených
- Max "99+" pro více než 99
- Klik → přejde na `/mobile/notifications`

## 🧪 Testování

### Velikosti obrazovek:
- [ ] 320px šířka (iPhone SE, malé Android)
- [ ] 360px šířka (běžné Android)
- [ ] 375px šířka (iPhone X/11/12)
- [ ] 414px šířka (iPhone Plus/Max)
- [ ] Landscape mode
- [ ] iPhone s notchem

### Funkčnost:
- [ ] Klik na logo → přejde na hlavní stránku
- [ ] Klik na mode toggle → zobrazí toast, reload s novým režimem
- [ ] Klik na notifikace → přejde na notifikace
- [ ] Klik na hamburger → otevře dropdown
- [ ] Klik mimo dropdown → zavře se
- [ ] Scroll → dropdown se zavře
- [ ] Escape → dropdown se zavře

### FIELD/FULL toggle:
- [ ] V FIELD režimu se zobrazuje grid ikona
- [ ] V FULL režimu se zobrazuje home ikona
- [ ] Po přepnutí se uloží do DB i cookie
- [ ] Po reloadu je správný režim
- [ ] Funguje i offline (cookie fallback)

## 📝 Poznámky

- Header je `position: sticky` pro lepší UX při scrollování
- Všechny buttony mají minimální touch target 40px (36px na malých obrazovkách)
- Dropdown používá backdrop-filter pro moderní vzhled
- Mode toggle má pulse animaci při přepínání
- Context processor automaticky načítá user a unread_count pro všechny templates

## ⚠️ Důležité

- **HTTPS je vyžadován** pro Speech Recognition (voice input)
- **Cookie fallback** pro mode switch funguje i offline
- **Safe area** podpora pro iOS notch je implementována
- **Legacy support** pro starou funkci `toggleMode()` je zachována
