import sqlite3
from flask import Flask, Blueprint, jsonify, request, render_template


# --- Brigádníci API ---
try:
    from flask import Blueprint, jsonify, request
except Exception:
    pass

def _gd_get_db():
    import os, sqlite3
    DB_PATH = os.environ.get('GD_DB_PATH', 'app.db')
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    return con

gd_brig_api = Blueprint('gd_brig_api', __name__)

@gd_brig_api.route('/gd/api/brigadnici', methods=['GET','POST'])
def _gd_brig_collection():
    con = _gd_get_db()
    cur = con.cursor()
    cur.execute('CREATE TABLE IF NOT EXISTS brigadnici (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL, role TEXT)')
    con.commit()
    if request.method == 'POST':
        data = request.get_json(force=True) or {}
        name = (data.get('name') or '').strip()
        role = (data.get('role') or 'Brigádník').strip()
        if not name:
            return jsonify({'error':'name required'}), 400
        cur.execute('INSERT INTO brigadnici (name, role) VALUES (?, ?)', (name, role))
        con.commit()
        return jsonify({'ok':True}), 201
    rows = cur.execute('SELECT id, name, role FROM brigadnici ORDER BY id DESC').fetchall()
    return jsonify([dict(r) for r in rows])

@gd_brig_api.route('/gd/api/brigadnici/<int:bid>', methods=['DELETE'])
def _gd_brig_delete(bid):
    con = _gd_get_db()
    cur = con.cursor()
    cur.execute('DELETE FROM brigadnici WHERE id=?', (bid,))
    con.commit()
    return jsonify({'ok':True})

# TODO: register blueprint: app.register_blueprint(gd_brig_api)


# --- Employees aliases (so navbar lands on the tabbed page) ---
from flask import render_template

@app.route('/zamestnanci')
@app.route('/zamestnanci/')
@app.route('/employees')
@app.route('/employees/')
def _gd_alias_employees():
    return render_template('employees.html')
