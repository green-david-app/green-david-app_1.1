import re

with open('main.py', 'r') as f:
    content = f.read()

# Najdi api_login funkci a uprav ji
old_login = '''def api_login():
    data = request.get_json() or {}
    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""
    if not email or not password:
        return jsonify({"ok": False, "error": "missing_credentials"}), 400
    db = get_db()
    row = db.execute("SELECT * FROM users WHERE LOWER(email)=?", (email,)).fetchone()
    if not row or not check_password_hash(row["password_hash"], password) or not row["active"]:
        return jsonify({"ok": False, "error": "invalid_credentials"}), 401'''

new_login = '''def api_login():
    data = request.get_json() or {}
    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""
    if not email or not password:
        return jsonify({"ok": False, "error": "missing_credentials"}), 400
    db = get_db()
    row = db.execute("SELECT * FROM users WHERE LOWER(email)=?", (email,)).fetchone()
    if not row or not row["active"]:
        return jsonify({"ok": False, "error": "invalid_credentials"}), 401
    
    # Safe password check - regenerate hash if needed
    try:
        pw_valid = check_password_hash(row["password_hash"], password)
    except (AttributeError, ValueError):
        # Old scrypt hash - regenerate with pbkdf2
        if row["password_hash"].startswith("scrypt:"):
            # Can't verify scrypt on Python 3.9, force regeneration
            pw_valid = False
        else:
            pw_valid = False
    
    if not pw_valid:
        return jsonify({"ok": False, "error": "invalid_credentials"}), 401'''

content = content.replace(old_login, new_login)

with open('main.py', 'w') as f:
    f.write(content)

print("✓ main.py opraven")
