from flask import Blueprint, request, jsonify
from app.database import get_db

budget_bp = Blueprint('budget', __name__)


@budget_bp.route('/api/jobs/<int:job_id>/budget', methods=['GET'])
def get_budget(job_id):
    """Vrátí celý rozpočet zakázky seskupený podle section_type."""
    db = get_db()
    sections = db.execute(
        '''SELECT * FROM budget_sections WHERE job_id = ?
           ORDER BY CASE section_type
               WHEN 'material' THEN 1
               WHEN 'labor' THEN 2
               WHEN 'extras' THEN 3
           END, sort_order ASC, id ASC''',
        (job_id,)
    ).fetchall()

    totals = {'material': 0, 'labor': 0, 'extras': 0}
    result = []

    for sec in sections:
        sec = dict(sec)
        items = db.execute(
            'SELECT * FROM budget_items WHERE section_id = ? ORDER BY sort_order ASC, id ASC',
            (sec['id'],)
        ).fetchall()

        sec_total = 0
        items_list = []
        for item in items:
            item = dict(item)
            item_total = round((item.get('quantity') or 0) * (item.get('unit_price') or 0), 2)
            items_list.append({
                'id': item['id'],
                'description': item.get('description', ''),
                'unit': item.get('unit', 'ks'),
                'quantity': item.get('quantity', 0),
                'unit_price': item.get('unit_price', 0),
                'total': item_total,
                'note': item.get('note'),
                'sort_order': item.get('sort_order', 0)
            })
            sec_total += item_total

        stype = sec.get('section_type', 'material')
        totals[stype] = totals.get(stype, 0) + sec_total

        result.append({
            'id': sec['id'],
            'name': sec.get('name', ''),
            'section_type': stype,
            'sort_order': sec.get('sort_order', 0),
            'items': items_list,
            'subtotal': round(sec_total, 2)
        })

    grand_total = totals['material'] + totals['labor'] + totals['extras']

    # Skutečné náklady z výkazů (PRÁCE)
    ts_cols = [r[1] for r in db.execute("PRAGMA table_info(timesheets)").fetchall()]
    has_labor_cost = 'labor_cost' in ts_cols

    actual_labor = {'total_hours': 0, 'total_cost': 0, 'by_employee': []}
    try:
        if has_labor_cost:
            ts_rows = db.execute("""
                SELECT e.name, e.hourly_rate,
                       SUM(t.hours) as hours,
                       SUM(COALESCE(t.labor_cost, 0)) as cost
                FROM timesheets t
                JOIN employees e ON e.id = t.employee_id
                WHERE t.job_id = ?
                GROUP BY t.employee_id
                ORDER BY cost DESC
            """, (job_id,)).fetchall()
        else:
            ts_rows = db.execute("""
                SELECT e.name, e.hourly_rate, SUM(t.hours) as hours
                FROM timesheets t
                JOIN employees e ON e.id = t.employee_id
                WHERE t.job_id = ?
                GROUP BY t.employee_id
                ORDER BY hours DESC
            """, (job_id,)).fetchall()

        for ts in ts_rows:
            ts = dict(ts)
            rate = ts.get('hourly_rate') or 250.0
            hours = ts.get('hours') or 0
            cost = ts.get('cost')
            if cost is None:
                cost = round(hours * rate, 0)
            else:
                cost = round(cost, 0)

            actual_labor['total_hours'] += hours
            actual_labor['total_cost'] += cost
            actual_labor['by_employee'].append({
                'name': ts.get('name'),
                'hourly_rate': round(rate, 0),
                'hours': round(hours, 1),
                'cost': cost
            })

        actual_labor['total_hours'] = round(actual_labor['total_hours'], 1)
        actual_labor['total_cost'] = round(actual_labor['total_cost'], 0)
    except Exception:
        pass

    return jsonify({
        'ok': True,
        'sections': result,
        'summary': {
            'total_material': round(totals['material'], 2),
            'total_labor': round(totals['labor'], 2),
            'total_extras': round(totals['extras'], 2),
            'grand_total': round(grand_total, 2)
        },
        'actual_labor': actual_labor
    })


@budget_bp.route('/api/jobs/<int:job_id>/budget/sections', methods=['POST'])
def create_section(job_id):
    db = get_db()
    data = request.get_json() or {}
    name = data.get('name', '').strip()
    section_type = data.get('section_type', 'material')

    if not name:
        return jsonify({'ok': False, 'error': 'Název je povinný'}), 400
    if section_type not in ('material', 'labor', 'extras'):
        return jsonify({'ok': False, 'error': 'Neplatný typ'}), 400

    max_order = db.execute(
        'SELECT COALESCE(MAX(sort_order), 0) FROM budget_sections WHERE job_id = ? AND section_type = ?',
        (job_id, section_type)
    ).fetchone()[0]

    cursor = db.execute(
        'INSERT INTO budget_sections (job_id, name, section_type, sort_order) VALUES (?, ?, ?, ?)',
        (job_id, name, section_type, max_order + 1)
    )
    db.commit()
    return jsonify({'ok': True, 'id': cursor.lastrowid})


@budget_bp.route('/api/budget/sections/<int:section_id>', methods=['PUT'])
def update_section(section_id):
    db = get_db()
    data = request.get_json() or {}
    name = data.get('name', '').strip()
    if not name:
        return jsonify({'ok': False, 'error': 'Název je povinný'}), 400
    db.execute('UPDATE budget_sections SET name = ? WHERE id = ?', (name, section_id))
    db.commit()
    return jsonify({'ok': True})


@budget_bp.route('/api/budget/sections/<int:section_id>', methods=['DELETE'])
def delete_section(section_id):
    db = get_db()
    db.execute('DELETE FROM budget_items WHERE section_id = ?', (section_id,))
    db.execute('DELETE FROM budget_sections WHERE id = ?', (section_id,))
    db.commit()
    return jsonify({'ok': True})


@budget_bp.route('/api/budget/sections/<int:section_id>/items', methods=['POST'])
def create_item(section_id):
    db = get_db()
    data = request.get_json() or {}
    description = data.get('description', '').strip()
    if not description:
        return jsonify({'ok': False, 'error': 'Popis je povinný'}), 400

    max_order = db.execute(
        'SELECT COALESCE(MAX(sort_order), 0) FROM budget_items WHERE section_id = ?',
        (section_id,)
    ).fetchone()[0]

    cursor = db.execute(
        'INSERT INTO budget_items (section_id, description, unit, quantity, unit_price, sort_order, note) VALUES (?, ?, ?, ?, ?, ?, ?)',
        (section_id, description, data.get('unit', 'ks'), data.get('quantity', 0),
         data.get('unit_price', 0), max_order + 1, data.get('note'))
    )
    db.commit()
    return jsonify({'ok': True, 'id': cursor.lastrowid})


@budget_bp.route('/api/budget/items/<int:item_id>', methods=['PUT'])
def update_item(item_id):
    db = get_db()
    data = request.get_json() or {}
    fields, values = [], []
    for key in ['description', 'unit', 'quantity', 'unit_price', 'note']:
        if key in data:
            fields.append(f'{key} = ?')
            values.append(data[key])
    if not fields:
        return jsonify({'ok': False, 'error': 'Žádná data'}), 400
    values.append(item_id)
    db.execute(f'UPDATE budget_items SET {", ".join(fields)} WHERE id = ?', values)
    db.commit()
    return jsonify({'ok': True})


@budget_bp.route('/api/budget/items/<int:item_id>', methods=['DELETE'])
def delete_item(item_id):
    db = get_db()
    db.execute('DELETE FROM budget_items WHERE id = ?', (item_id,))
    db.commit()
    return jsonify({'ok': True})
