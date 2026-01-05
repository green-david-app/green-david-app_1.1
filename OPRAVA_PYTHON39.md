# OPRAVA PRO PYTHON 3.9

## Problém
- Python 3.9 nemá `hashlib.scrypt`
- Hesla v databázi byla uložená se scrypt hashem
- Login nefungoval (500 Internal Server Error)

## Řešení
1. Opravený `main.py` - používá `pbkdf2:sha256` místo `scrypt`
2. Migrační skript `migrate_passwords.py` - přegeneruje hesla v databázi

## JAK TO SPUSTIT

### 1. Ujisti se že máš správné verze balíčků:

```bash
pip3 uninstall werkzeug
pip3 install werkzeug==2.3.7
```

### 2. Spusť migrační skript:

```bash
cd /Users/greendavid/Desktop/green-david-WORK
python3 migrate_passwords.py
```

Měl bys vidět:
```
✓ admin@greendavid.local -> nové heslo: admin123
✓ admin@greendavid.cz -> nové heslo: admin123
✓ david@greendavid.cz -> nové heslo: admin123
```

### 3. Spusť aplikaci:

```bash
python3 main.py
```

### 4. Přihlaš se v Safari:

- URL: `127.0.0.1:5000`
- Email: `admin@greendavid.local`
- Heslo: `admin123`

## Pokud to stále nefunguje

Vytvoř úplně nový účet:

```bash
python3 << 'EOF'
import sqlite3
from werkzeug.security import generate_password_hash

db = sqlite3.connect('app.db')
db.execute("DELETE FROM users WHERE email = 'test@test.cz'")
db.execute("""
    INSERT INTO users (email, name, role, password_hash, approved, active, created_at)
    VALUES (?, ?, ?, ?, 1, 1, datetime('now'))
""", ('test@test.cz', 'Test Admin', 'owner', 
      generate_password_hash('test123', method='pbkdf2:sha256')))
db.commit()
print("✓ Vytvořen účet: test@test.cz / test123")
db.close()
EOF
```

Pak se přihlaš s: `test@test.cz` / `test123`
