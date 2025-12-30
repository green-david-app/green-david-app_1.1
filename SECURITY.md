# Bezpečnostní checklist pro Green David App

## 🔒 Před nasazením do produkce

### Kritické - MUSÍ být provedeno

- [ ] **SECRET_KEY** - Vygenerovat silný tajný klíč a nastavit v ENV
  ```bash
  python -c "import secrets; print(secrets.token_hex(32))"
  ```

- [ ] **Admin heslo** - Změnit výchozí admin heslo ihned po první přihlášení

- [ ] **HTTPS** - Nasadit pouze přes HTTPS (nikdy HTTP v produkci)

- [ ] **Databáze** - Pravidelné zálohování databáze
  ```bash
  cp app.db backups/app-$(date +%Y%m%d-%H%M%S).db
  ```

- [ ] **Logs** - Zkontrolovat, že citlivé údaje nejsou logovány (hesla, tokeny)

- [ ] **File uploads** - Validovat a limitovat nahrávané soubory

### Doporučené

- [ ] **Rate limiting** - Omezit počet pokusů o přihlášení
  ```python
  from flask_limiter import Limiter
  limiter = Limiter(app, default_limits=["200 per day", "50 per hour"])
  ```

- [ ] **CORS** - Omezit CORS pouze na důvěryhodné domény

- [ ] **SQL Injection** - Vždy používat parametrizované dotazy (✅ opraveno)

- [ ] **XSS Protection** - Escapovat všechen uživatelský vstup v templates

- [ ] **CSRF Protection** - Přidat Flask-WTF pro CSRF tokeny

- [ ] **Session security** - Nastavit secure cookies (✅ opraveno)

## 🛡️ Bezpečnostní vylepšení v opravené verzi

### Co bylo opraveno:

1. **Validace vstupů**
   - ✅ Validace emailu
   - ✅ Validace hodin (0-24)
   - ✅ Sanitizace názvů souborů

2. **Error handling**
   - ✅ Strukturované logování
   - ✅ Try-catch bloky kolem DB operací
   - ✅ Rollback při chybách

3. **Authentication**
   - ✅ Secure session cookies
   - ✅ Password hashing (bcrypt)
   - ✅ Role-based access control

4. **Database**
   - ✅ Parametrizované SQL dotazy
   - ✅ Foreign key constraints
   - ✅ Indexy pro výkon

5. **Configuration**
   - ✅ Environment variables
   - ✅ Oddělení konfigurace od kódu
   - ✅ Bezpečné výchozí hodnoty

## 📊 Monitoring a údržba

### Denně
- Kontrola logů (`app.log`)
- Monitorování místa na disku

### Týdně
- Zálohování databáze
- Kontrola neúspěšných přihlášení

### Měsíčně
- Aktualizace závislostí
- Bezpečnostní audit
- Rotace logů

## 🚨 V případě bezpečnostního incidentu

1. **Okamžitě**
   - Vypnout aplikaci
   - Změnit všechna hesla
   - Analyzovat logy

2. **Pak**
   - Obnovit ze zálohy
   - Identifikovat zranitelnost
   - Opravit a otestovat
   - Znovu nasadit

3. **Nakonec**
   - Informovat uživatele
   - Dokumentovat incident
   - Zlepšit procesy

## 📞 Kontakty

V případě nalezení bezpečnostní chyby:
- Email: security@greendavid.cz
- GitHub Issues (pouze pro nekritické problémy)

## 📚 Užitečné odkazy

- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [Flask Security Best Practices](https://flask.palletsprojects.com/en/3.0.x/security/)
- [Python Security](https://python.readthedocs.io/en/stable/library/security_warnings.html)
