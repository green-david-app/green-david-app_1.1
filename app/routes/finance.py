# Green David App - Finance routes (invoices)
from flask import Blueprint, request, jsonify
from datetime import datetime
from app.database import get_db

finance_bp = Blueprint('finance', __name__)


def _row_to_invoice(row):
    """Convert DB row to invoice dict."""
    if row is None:
        return None
    return {
        "id": row["id"],
        "type": row["type"] or "issued",
        "number": row["number"] or "",
        "client": row["client"] or "",
        "supplier": row["supplier"] or "",
        "amount": float(row["amount"] or 0),
        "date": row["date"] or "",
        "due_date": row["due_date"] or None,
        "status": row["status"] or "pending",
        "note": row["note"] or "",
        "created_at": row["created_at"] or "",
        "updated_at": row["updated_at"] or "",
    }


@finance_bp.route("/api/invoices", methods=["GET"])
def get_invoices():
    """GET /api/invoices - list all invoices."""
    db = get_db()
    rows = db.execute(
        "SELECT * FROM invoices ORDER BY created_at DESC"
    ).fetchall()
    invoices = [_row_to_invoice(r) for r in rows]
    return jsonify({"ok": True, "invoices": invoices})


@finance_bp.route("/api/invoices", methods=["POST"])
def create_invoice():
    """POST /api/invoices - create new invoice."""
    data = request.get_json() or {}
    db = get_db()

    number = (data.get("number") or "").strip()
    if not number:
        return jsonify({"ok": False, "error": "Číslo faktury je povinné"}), 400

    type_ = data.get("type", "issued")
    client = (data.get("client") or "").strip() if type_ == "issued" else ""
    supplier = (data.get("supplier") or "").strip() if type_ == "received" else ""
    amount = float(data.get("amount") or 0)
    date = data.get("date") or datetime.now().strftime("%Y-%m-%d")
    due_date = data.get("due_date") or None
    status = data.get("status", "pending")
    note = (data.get("note") or "").strip()

    now = datetime.now().isoformat()
    db.execute(
        """INSERT INTO invoices (type, number, client, supplier, amount, date, due_date, status, note, created_at, updated_at)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (type_, number, client, supplier, amount, date, due_date, status, note, now, now),
    )
    db.commit()
    row_id = db.execute("SELECT last_insert_rowid()").fetchone()[0]
    row = db.execute("SELECT * FROM invoices WHERE id = ?", (row_id,)).fetchone()
    return jsonify({"ok": True, "invoice": _row_to_invoice(row)})


@finance_bp.route("/api/invoices/<int:invoice_id>", methods=["PATCH"])
def update_invoice(invoice_id):
    """PATCH /api/invoices/<id> - update invoice."""
    data = request.get_json() or {}
    db = get_db()

    row = db.execute("SELECT * FROM invoices WHERE id = ?", (invoice_id,)).fetchone()
    if not row:
        return jsonify({"ok": False, "error": "Faktura nenalezena"}), 404

    type_ = data.get("type", row["type"])
    number = (data.get("number") or row["number"] or "").strip()
    if not number:
        return jsonify({"ok": False, "error": "Číslo faktury je povinné"}), 400

    client = (data.get("client") or "").strip() if type_ == "issued" else ""
    supplier = (data.get("supplier") or "").strip() if type_ == "received" else ""
    amount = float(data.get("amount") or row["amount"] or 0)
    date = data.get("date") or row["date"] or ""
    due_date = data.get("due_date") if "due_date" in data else row["due_date"]
    status = data.get("status", row["status"])
    note = (data.get("note") or "").strip()

    now = datetime.now().isoformat()
    db.execute(
        """UPDATE invoices SET type=?, number=?, client=?, supplier=?, amount=?, date=?, due_date=?, status=?, note=?, updated_at=?
           WHERE id=?""",
        (type_, number, client, supplier, amount, date, due_date, status, note, now, invoice_id),
    )
    db.commit()
    row = db.execute("SELECT * FROM invoices WHERE id = ?", (invoice_id,)).fetchone()
    return jsonify({"ok": True, "invoice": _row_to_invoice(row)})


@finance_bp.route("/api/invoices/<int:invoice_id>", methods=["DELETE"])
def delete_invoice(invoice_id):
    """DELETE /api/invoices/<id> - delete invoice."""
    db = get_db()
    cur = db.execute("DELETE FROM invoices WHERE id = ?", (invoice_id,))
    db.commit()
    if cur.rowcount == 0:
        return jsonify({"ok": False, "error": "Faktura nenalezena"}), 404
    return jsonify({"ok": True})
