#!/usr/bin/env python3
"""
Generátor bezpečného SECRET_KEY pro Flask aplikaci
Použití: python generate_secret_key.py
"""

import secrets

def generate_secret_key(length=32):
    """Vygeneruje bezpečný náhodný SECRET_KEY"""
    return secrets.token_hex(length)

if __name__ == "__main__":
    key = generate_secret_key()
    print("=" * 70)
    print("🔐 VYGENEROVANÝ SECRET_KEY (uložte do .env souboru)")
    print("=" * 70)
    print()
    print(f"SECRET_KEY={key}")
    print()
    print("=" * 70)
    print("⚠️  NIKDY NECOMMITUJTE TENTO KLÍČ DO GITU!")
    print("=" * 70)
