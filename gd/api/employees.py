import sqlite3
from flask import jsonify, request

# Helper to get DB (expects app.config["GD_DB_PATH"] or default app.db in project root)
def _get_db_path(app):
    return app.config.get("GD_DB_PATH", "app.db")

def _query(conn, sql, params=(), commit=False):
    cur = conn.cursor()
    cur.execute(sql, params)
    if commit:
        conn.commit()
    return cur

def _row_to_dict(cursor, row):
    return {d[0]: row[i] for i, d in enumerate(cursor.description)}

def _ensure_tables(conn):
    # Minimal safeguard: ensure temps table exists
    _query(conn, """
    CREATE TABLE IF NOT EXISTS temps (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        first_name TEXT NOT NULL,
        last_name TEXT NOT NULL,
        phone TEXT,
        email TEXT,
        hourly_rate REAL NOT NULL DEFAULT 0,
        active INTEGER NOT NULL DEFAULT 1,
        notes TEXT,
        created_at TEXT DEFAULT (datetime('now')),
        updated_at TEXT DEFAULT (datetime('now'))
    );
    """, commit=True)

def register_api(app, bp):
    db_path = _get_db_path(app)

    # --- Zaměstnanci (basic stubs to avoid breaking existing calls) ---
    @bp.get('/employees')
    def list_employees():
        # If you already have an employees table, adapt this to your schema.
        # Here we return an empty list as a non-breaking stub.
        return jsonify([])

    # --- Brigádníci ---
    @bp.get('/temps')
    def list_temps():
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        _ensure_tables(conn)
        cur = _query(conn, "SELECT id, first_name, last_name, phone, email, hourly_rate, active, notes, created_at, updated_at FROM temps ORDER BY last_name, first_name")
        rows = [dict(r) for r in cur.fetchall()]
        conn.close()
        return jsonify(rows)

    @bp.post('/temps')
    def create_temp():
        data = request.get_json(force=True) or {}
        required = ['first_name', 'last_name']
        for k in required:
            if not data.get(k):
                return jsonify({'error': f'Chybí povinné pole: {k}'}), 400
        hourly_rate = float(data.get('hourly_rate') or 0)
        conn = sqlite3.connect(db_path)
        _ensure_tables(conn)
        cur = _query(conn, """
            INSERT INTO temps (first_name, last_name, phone, email, hourly_rate, active, notes, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, datetime('now'))
        """, (data.get('first_name'), data.get('last_name'), data.get('phone'), data.get('email'),
               hourly_rate, 1 if data.get('active', True) else 0, data.get('notes')), commit=True)
        new_id = cur.lastrowid
        conn.close()
        return jsonify({'id': new_id}), 201

    @bp.get('/temps/<int:temp_id>')
    def get_temp(temp_id):
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        _ensure_tables(conn)
        cur = _query(conn, "SELECT * FROM temps WHERE id=?", (temp_id,))
        row = cur.fetchone()
        conn.close()
        if not row:
            return jsonify({'error': 'Nenalezeno'}), 404
        return jsonify(dict(row))

    @bp.put('/temps/<int:temp_id>')
    def update_temp(temp_id):
        data = request.get_json(force=True) or {}
        fields = ['first_name', 'last_name', 'phone', 'email', 'hourly_rate', 'active', 'notes']
        sets, params = [], []
        for f in fields:
            if f in data:
                sets.append(f"{f}=?")
                if f == 'active':
                    params.append(1 if data[f] else 0)
                else:
                    params.append(data[f])
        if not sets:
            return jsonify({'error': 'Nic k aktualizaci'}), 400
        params.append(temp_id)
        conn = sqlite3.connect(db_path)
        _ensure_tables(conn)
        _query(conn, f"UPDATE temps SET {', '.join(sets)}, updated_at=datetime('now') WHERE id=?", tuple(params), commit=True)
        conn.close()
        return jsonify({'ok': True})

    @bp.delete('/temps/<int:temp_id>')
    def delete_temp(temp_id):
        conn = sqlite3.connect(db_path)
        _ensure_tables(conn)
        _query(conn, "DELETE FROM temps WHERE id=?", (temp_id,), commit=True)
        conn.close()
        return jsonify({'ok': True})

    @bp.get('/temps/export.csv')
    def export_temps_csv():
        # Simple CSV export
        import csv, io
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        _ensure_tables(conn)
        cur = _query(conn, "SELECT id, first_name, last_name, phone, email, hourly_rate, active, notes FROM temps ORDER BY last_name, first_name")
        rows = cur.fetchall()
        conn.close()
        buf = io.StringIO()
        writer = csv.writer(buf)
        writer.writerow(['ID', 'Jméno', 'Příjmení', 'Telefon', 'E-mail', 'Hodinová sazba', 'Aktivní', 'Poznámka'])
        for r in rows:
            writer.writerow([r['id'], r['first_name'], r['last_name'], r['phone'], r['email'], r['hourly_rate'], 'ano' if r['active'] else 'ne', r['notes']])
        return app.response_class(buf.getvalue(), mimetype='text/csv')
