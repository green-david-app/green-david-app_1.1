
# Registers a safe "/search" endpoint on the existing Flask app without editing main.py.
# It attempts to reuse main.py's sqlite connection helpers if available.
# No "Markup" import to keep Flask 3.x compatible.

from flask import request, Response
import sqlite3
import html

# Import the already-created app from main.py
try:
    from main import app  # type: ignore
except Exception as e:
    raise RuntimeError(f"search_fix.py: cannot import app from main.py: {e}")

# Try to import a DB helper if main.py exposes one
get_db = None
db_path = None
try:
    from main import get_db  # type: ignore
except Exception:
    get_db = None

try:
    from main import DB_PATH as _DB_PATH  # type: ignore
    db_path = _DB_PATH
except Exception:
    db_path = None

def _connect():
    if get_db:
        try:
            return get_db()
        except Exception:
            pass
    # Fallback: open sqlite in application root
    path = db_path or "app.db"
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    return conn

def _query(sql, params=()):
    conn = _connect()
    try:
        cur = conn.execute(sql, params)
        rows = cur.fetchall()
        return rows
    finally:
        try:
            conn.close()
        except Exception:
            pass

def _row(r, key, default=""):
    try:
        v = r[key]
    except Exception:
        return default
    return v if v is not None else default

@app.route("/search")
def search_page():
    q = request.args.get("q", "").strip()
    like = f"%{q}%"
    # Be conservative: select only safe, existing columns
    rows = _query(
        "SELECT id, name, city, code FROM jobs "
        "WHERE (name LIKE ? OR city LIKE ? OR code LIKE ?) "
        "ORDER BY id DESC LIMIT 100",
        (like, like, like),
    )
    # Render ultra-simple HTML so the page always loads
    out = []
    out.append("<!doctype html><meta charset='utf-8'><title>Výsledky hledání</title>")
    out.append("<style>body{font-family:system-ui,-apple-system,Segoe UI,Roboto,Ubuntu,Arial,sans-serif;background:#f5f7f7;color:#222;margin:24px;}")
    out.append(".wrap{max-width:980px;margin:0 auto;} h1{font-size:22px;margin:0 0 12px;} form{display:flex;gap:8px;margin:12px 0 24px;}")
    out.append("input[type=text]{flex:1;padding:10px 12px;border-radius:8px;border:1px solid #cfd4d7;background:#fff;color:#111;}")
    out.append("button{padding:10px 14px;border-radius:8px;border:0;background:#2bb673;color:white;font-weight:600;cursor:pointer;}")
    out.append(".card{background:white;border:1px solid #e5eaec;border-radius:12px;padding:12px 14px;margin:8px 0;} .muted{opacity:.7;font-size:12px;}")
    out.append("a{color:#0b5;} .rowtop{display:flex;justify-content:space-between;gap:12px;align-items:center;} .code{font-family:ui-monospace,Menlo,Consolas,monospace}</style>")
    out.append("<div class='wrap'>")
    out.append(f"<h1>Hledat</h1>")
    out.append("<form action='/search' method='get'><input type='text' name='q' placeholder='hledat…' value='" + html.escape(q) + "'><button>Hledat</button></form>")
    if not rows:
        out.append("<p class='muted'>Žádné výsledky.</p>")
    else:
        for r in rows:
            rid = _row(r, 'id')
            name = html.escape(str(_row(r, 'name', '')))
            city = html.escape(str(_row(r, 'city', '')))
            code = html.escape(str(_row(r, 'code', '')))
            out.append("<div class='card'>")
            out.append(f"<div class='rowtop'><strong>{name or '(bez názvu)'}</strong><span class='muted code'>#{rid}</span></div>")
            extra = []
            if city: extra.append(city)
            if code: extra.append(code)
            if extra:
                out.append("<div class='muted'>" + " • ".join(extra) + "</div>")
            out.append("</div>")
    out.append("</div>")
    html_text = "".join(out)
    return Response(html_text, mimetype="text/html; charset=utf-8")
