#!/usr/bin/env python3
"""
Migrace hesel z scrypt na pbkdf2:sha256 pro Python 3.9 kompatibilitu
"""
import sqlite3
import os
from werkzeug.security import generate_password_hash

# Konfigurace
DB_PATH = "app.db"

# Default hesla pro admin účty (pouze pro migraci)
DEFAULT_PASSWORDS = {
    'admin@greendavid.local': 'admin123',
    'admin@greendavid.cz': 'admin123',
    'david@greendavid.cz': 'admin123',
    'david@test.cz': 'admin123',  # Přidáno pro migraci
}

def migrate_passwords():
    """Přegeneruje všechna hesla na pbkdf2:sha256"""
    
    if not os.path.exists(DB_PATH):
        print(f"❌ Databáze {DB_PATH} neexistuje!")
        return False
    
    db = sqlite3.connect(DB_PATH)
    db.row_factory = sqlite3.Row
    
    # Získej všechny uživatele
    users = db.execute("SELECT id, email, password_hash FROM users").fetchall()
    
    print(f"Nalezeno {len(users)} uživatelů\n")
    
    migrated = 0
    for user in users:
        email = user['email']
        old_hash = user['password_hash']
        
        # Kontrola jestli je to scrypt hash
        if old_hash and old_hash.startswith('scrypt:'):
            # Pokud máme default heslo, použijeme ho
            if email in DEFAULT_PASSWORDS:
                new_password = DEFAULT_PASSWORDS[email]
                new_hash = generate_password_hash(new_password, method='pbkdf2:sha256')
                
                db.execute(
                    "UPDATE users SET password_hash = ? WHERE id = ?",
                    (new_hash, user['id'])
                )
                
                print(f"✓ {email:40} -> nové heslo: {new_password}")
                migrated += 1
            else:
                print(f"⚠ {email:40} -> NELZE MIGROVAT (neznámé heslo)")
        elif old_hash and old_hash.startswith('pbkdf2:'):
            print(f"  {email:40} -> již pbkdf2 (OK)")
        else:
            print(f"⚠ {email:40} -> neznámý formát hashe")
    
    db.commit()
    db.close()
    
    print(f"\n✓ Migrováno {migrated} hesel")
    print("\nNová hesla:")
    for email, pwd in DEFAULT_PASSWORDS.items():
        print(f"  {email}: {pwd}")
    
    return True

if __name__ == "__main__":
    print("=" * 70)
    print("MIGRACE HESEL: scrypt -> pbkdf2:sha256")
    print("=" * 70)
    print()
    
    success = migrate_passwords()
    
    if success:
        print("\n" + "=" * 70)
        print("HOTOVO! Teď spusť aplikaci: python3 main.py")
        print("=" * 70)
    else:
        print("\n❌ Migrace selhala!")
