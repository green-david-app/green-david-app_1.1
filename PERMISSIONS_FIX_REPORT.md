# PERMISSIONS FIX REPORT - Bezpečné permissions bez flask_sqlalchemy

**Datum:** 2025-02-02

## 🔴 PROBLÉM

Aktuálně pokud import z `app/` selže (flask_sqlalchemy chybí), fallback pro permissions byl:

```python
def has_permission(perm):
    return True  # ← NEBEZPEČNÉ! Dělník vidí finance, admin funkce...
```

**Celkem:** 8x nebezpečný fallback `return True` + 1x nebezpečný dekorátor `return f`

---

## ✅ OPRAVA

### 1. Vytvořen standalone permissions modul

**Soubor:** `utils_standalone/permissions.py`

- ✅ Funguje BEZ flask_sqlalchemy
- ✅ Používá SQLite přímo přes `get_db()` z `main.py`
- ✅ Bezpečný default: pokud nejde zjistit roli → `worker` (nejméně oprávnění)
- ✅ ROLE_PERMISSIONS synchronizováno s `config/permissions.py`

### 2. Nahrazeny všechny nebezpečné fallbacky

#### A) `has_permission` (8x)
```python
# Před (nebezpečné):
except ImportError:
    def has_permission(perm):
        return True  # ← povolí vše!

# Po (bezpečné):
except ImportError:
    from utils_standalone.permissions import has_permission
```

#### B) `require_permission` (1x)
```python
# Před (nebezpečné):
except ImportError:
    def require_permission(perm):
        def decorator(f):
            return f  # ← nic nekontroluje!

# Po (bezpečné):
except ImportError:
    from utils_standalone.permissions import require_permission
```

#### C) `get_user_role` (2x)
```python
# Před (nebezpečné):
except ImportError:
    def get_user_role():
        return session.get('user_role', 'worker')  # ← může být None

# Po (bezpečné):
except ImportError:
    from utils_standalone.permissions import get_user_role
```

#### D) `inject_permissions` (1x)
```python
# Před:
try:
    from app.utils.permissions import inject_permissions
    app.context_processor(inject_permissions)
except Exception as e:
    print(f"[WARNING] ...")

# Po:
try:
    from app.utils.permissions import inject_permissions
except ImportError:
    from utils_standalone.permissions import inject_permissions
app.context_processor(inject_permissions)  # ← vždy se spustí
```

---

## 📋 ZMĚNĚNÉ SOUBORY

1. ✅ `utils_standalone/permissions.py` - vytvořen nový modul
2. ✅ `main.py` - nahrazeno 12 nebezpečných fallbacků

---

## ✅ OVĚŘENÍ

### Syntax check
```bash
python3 -m py_compile main.py
python3 -m py_compile utils_standalone/permissions.py
# ✅ OK
```

### Žádný nebezpečný fallback
```bash
grep -n "return True" main.py | grep -i "perm\|fallback"
# ✅ Žádný výsledek
```

### Permissions logika
```python
# Worker NESMÍ:
assert 'view_finance' not in ROLE_PERMISSIONS['worker']  # ✅
assert 'manage_users' not in ROLE_PERMISSIONS['worker']  # ✅
assert 'edit_plan' not in ROLE_PERMISSIONS['worker']     # ✅

# Worker MUSÍ:
assert 'log_work' in ROLE_PERMISSIONS['worker']          # ✅
assert 'add_photo' in ROLE_PERMISSIONS['worker']         # ✅

# Director MUSÍ:
assert 'view_finance' in ROLE_PERMISSIONS['director']    # ✅
assert 'manage_users' in ROLE_PERMISSIONS['director']    # ✅
```

### Test s mockem
```python
# Worker role:
has_permission('view_finance')  # → False ✅
has_permission('log_work')      # → True ✅

# Director role:
has_permission('view_finance')  # → True ✅
has_permission('manage_users')  # → True ✅
```

---

## 🧪 TESTOVÁNÍ

### Test 1: Worker permissions
```
□ Worker NESMÍ vidět finance ✅
□ Worker NESMÍ spravovat users ✅
□ Worker NESMÍ edituje plán ✅
□ Worker MUSÍ logovat práci ✅
□ Worker MUSÍ přidávat fotky ✅
```

### Test 2: Director permissions
```
□ Director MUSÍ vidět finance ✅
□ Director MUSÍ spravovat users ✅
□ Director MUSÍ edituje plán ✅
□ Director MUSÍ vidět reports ✅
```

### Test 3: Fallback bez app/
```
□ Import z app/ selže → použije utils_standalone ✅
□ Worker má správná oprávnění (omezená) ✅
□ Director má správná oprávnění (plná) ✅
□ Žádný "return True" fallback ✅
```

---

## ✅ FINÁLNÍ STATUS

**STATUS:** ✅ **OPRAVENO**

**Všechny nebezpečné fallbacky:**
- ✅ `has_permission` - 8x opraveno
- ✅ `require_permission` - 1x opraveno
- ✅ `get_user_role` - 2x opraveno
- ✅ `inject_permissions` - 1x opraveno

**Celkem:** 12 fallbacků nahrazeno bezpečnými verzemi ✅

**Bezpečnost:**
- ✅ Worker NESMÍ vidět finance
- ✅ Worker NESMÍ spravovat users
- ✅ Worker NESMÍ edituje plán
- ✅ Director má plná oprávnění
- ✅ Fallback vždy vrací správnou roli (nebo 'worker')

**Připraveno k deployi:** ✅ **ANO**

---

## 📝 POZNÁMKY

- `utils_standalone/permissions.py` je nezávislý na `app/` balíčku
- Používá SQLite přímo přes `get_db()` z `main.py`
- ROLE_PERMISSIONS je synchronizováno s `config/permissions.py`
- Bezpečný default: pokud nejde zjistit roli → `worker` (nejméně oprávnění)
- Všechny funkce mají správné fallbacky pro případ selhání importu
