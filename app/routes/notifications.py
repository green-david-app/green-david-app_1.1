# Green David App
from flask import Blueprint, jsonify, request
from datetime import datetime, timedelta
from app.database import get_db
from app.utils.permissions import require_auth, normalize_role

notifications_bp = Blueprint('notifications', __name__)


def create_job_notification(user_id, job_id, kind, title, body, entity_type='job', entity_id=None):
    """Helper function to create a notification for a job"""
    try:
        db = get_db()
        # Check if notification already exists
        existing = db.execute("""
            SELECT id FROM notifications
            WHERE user_id = ? AND entity_type = ? AND entity_id = ? AND kind = ? AND is_read = 0
            AND created_at >= datetime('now', '-1 day')
        """, (user_id, entity_type, entity_id or job_id, kind)).fetchone()
        
        if not existing:
            db.execute("""
                INSERT INTO notifications (user_id, kind, title, body, entity_type, entity_id, is_read, created_at)
                VALUES (?, ?, ?, ?, ?, ?, 0, datetime('now'))
            """, (user_id, kind, title, body, entity_type, entity_id or job_id))
            db.commit()
            return True
    except Exception as e:
        print(f"[NOTIF] Error creating notification: {e}")
    return False


def generate_auto_notifications(user_id):
    """Automaticky generuje notifikace pro blížící se termíny a důležité události."""
    db = get_db()
    now = datetime.now()
    today = now.strftime('%Y-%m-%d')
    tomorrow = (now + timedelta(days=1)).strftime('%Y-%m-%d')
    week_later = (now + timedelta(days=7)).strftime('%Y-%m-%d')
    
    # Získej existující notifikace, abychom nevytvářeli duplikáty
    existing = db.execute(
        "SELECT entity_type, entity_id, kind FROM notifications WHERE user_id=? AND created_at > datetime('now', '-24 hours')",
        (user_id,)
    ).fetchall()
    existing_keys = set((r['entity_type'], r['entity_id'], r['kind']) for r in existing)
    
    notifications_to_add = []
    
    # 1. Úkoly s blížícím se termínem (dnes nebo zítra)
    tasks = db.execute("""
        SELECT t.*, j.client as job_name FROM tasks t
        LEFT JOIN jobs j ON t.job_id = j.id
        WHERE t.status != 'done' AND t.deadline IS NOT NULL
        AND date(t.deadline) BETWEEN ? AND ?
    """, (today, tomorrow)).fetchall()
    
    for task in tasks:
        if ('task', task['id'], 'deadline') not in existing_keys:
            deadline_date = task['deadline'][:10] if task['deadline'] else ''
            is_today = deadline_date == today
            notifications_to_add.append({
                'user_id': user_id,
                'title': '⏰ Termín ' + ('DNES!' if is_today else 'zítra'),
                'body': f"{task['title']}" + (f" ({task['job_name']})" if task['job_name'] else ""),
                'kind': 'deadline',
                'entity_type': 'task',
                'entity_id': task['id']
            })
    
    # 2. Zakázky bez přiřazených zaměstnanců
    jobs_no_employees = db.execute("""
        SELECT j.* FROM jobs j
        LEFT JOIN job_employees je ON j.id = je.job_id
        WHERE j.status NOT IN ('completed', 'archived', 'cancelled')
        AND je.id IS NULL
        LIMIT 5
    """).fetchall()
    
    for job in jobs_no_employees:
        if ('job', job['id'], 'warning') not in existing_keys:
            job_name = job['client'] or job['name'] or f"#{job['id']}"
            notifications_to_add.append({
                'user_id': user_id,
                'title': '⚠️ Chybí přiřazení',
                'body': f"Zakázka '{job_name}' nemá přiřazené zaměstnance",
                'kind': 'warning',
                'entity_type': 'job',
                'entity_id': job['id']
            })
    
    # 3. Zakázky s blížícím se termínem (do 7 dnů)
    jobs_deadline = db.execute("""
        SELECT * FROM jobs 
        WHERE status NOT IN ('completed', 'archived', 'cancelled')
        AND deadline IS NOT NULL
        AND date(deadline) BETWEEN ? AND ?
    """, (today, week_later)).fetchall()
    
    for job in jobs_deadline:
        if ('job', job['id'], 'deadline') not in existing_keys:
            deadline_date = job['deadline'][:10] if job['deadline'] else ''
            days_left = (datetime.strptime(deadline_date, '%Y-%m-%d') - now).days
            job_name = job['client'] or job['name'] or f"Zakázka #{job['id']}"
            notifications_to_add.append({
                'user_id': user_id,
                'title': '📅 Termín zakázky' + (' DNES!' if days_left == 0 else f' za {days_left} dní'),
                'body': job_name,
                'kind': 'deadline',
                'entity_type': 'job',
                'entity_id': job['id']
            })
    
    # 4. Nízké zásoby materiálu
    try:
        low_stock = db.execute("""
            SELECT * FROM warehouse_items 
            WHERE quantity <= min_quantity AND min_quantity > 0
            LIMIT 5
        """).fetchall()
        
        for item in low_stock:
            if ('stock', item['id'], 'stock') not in existing_keys:
                notifications_to_add.append({
                    'user_id': user_id,
                    'title': '📦 Nízké zásoby',
                    'body': f"{item['name']}: zbývá {item['quantity']} {item.get('unit', 'ks')}",
                    'kind': 'stock',
                    'entity_type': 'stock',
                    'entity_id': item['id']
                })
    except:
        pass  # Tabulka warehouse_items nemusí existovat
    
    # Job-specific critical notifications
    try:
        critical_jobs = db.execute("""
            SELECT j.id, j.title, j.deadline, j.budget, j.actual_value, j.status
            FROM jobs j
            WHERE j.status NOT IN ('completed', 'archived', 'cancelled')
        """, ()).fetchall()
        
        for job in critical_jobs:
            job = dict(job)
            deadline = job.get('deadline')
            budget = job.get('budget') or 0
            actual = job.get('actual_value') or 0
            
            # Deadline critical
            if deadline:
                try:
                    deadline_dt = datetime.strptime(deadline[:10], '%Y-%m-%d').date()
                    days_until = (deadline_dt - today).days
                    
                    if days_until < 0:
                        create_job_notification(
                            user_id, job['id'], 'deadline',
                            f'🚨 Zakázka "{job.get("title") or job.get("name") or "Bez názvu"}" je po termínu',
                            f'Zakázka je {abs(days_until)} dní po termínu. Okamžitá akce vyžadována.',
                            'job', job['id']
                        )
                    elif days_until <= 3:
                        create_job_notification(
                            user_id, job['id'], 'deadline',
                            f'⏰ Kritický deadline: "{job.get("title") or job.get("name") or "Bez názvu"}"',
                            f'Zbývá pouze {days_until} dní do deadline. Zkontrolujte průběh.',
                            'job', job['id']
                        )
                except:
                    pass
            
            # Budget critical
            if budget > 0:
                spent_pct = (actual / budget) * 100
                if spent_pct > 90:
                    create_job_notification(
                        user_id, job['id'], 'budget',
                        f'💰 Rozpočet téměř vyčerpán: "{job.get("title") or job.get("name") or "Bez názvu"}"',
                        f'Rozpočet je vyčerpán na {spent_pct:.1f}%. Zkontrolujte další výdaje.',
                        'job', job['id']
                    )
    except Exception as e:
        print(f"[NOTIF] Job notifications error: {e}")
    
    # Vlož nové notifikace
    for n in notifications_to_add[:10]:  # Max 10 najednou
        try:
            db.execute("""
                INSERT INTO notifications (user_id, title, body, kind, entity_type, entity_id, is_read, created_at)
                VALUES (?, ?, ?, ?, ?, ?, 0, datetime('now'))
            """, (n['user_id'], n['title'], n['body'], n['kind'], n['entity_type'], n['entity_id']))
        except:
            pass
    
    if notifications_to_add:
        db.commit()


@notifications_bp.route("/api/notifications", methods=["GET", "PATCH", "DELETE"])
def api_notifications():
    """In-app notifications for the current signed-in user.

    GET: list notifications
      - unread_only=1
      - limit=50 (max 200)
    PATCH: mark read
      - id: single notification id
      - all=1: mark all as read
    DELETE: delete
      - id: single id
      - all=1: delete all (dangerous - owner only)
    """
    u, err = require_auth()
    if err:
        return err
    db = get_db()

    if request.method == "GET":
        # Automaticky generuj notifikace
        try:
            generate_auto_notifications(int(u["id"]))
        except Exception as e:
            print(f"[NOTIF] Auto-generate error: {e}")
        
        unread_only = str(request.args.get("unread_only") or "").strip() in ("1", "true", "yes")
        limit = request.args.get("limit", type=int) or 50
        limit = max(1, min(int(limit), 200))

        conds = ["(n.user_id=? OR n.employee_id IN (SELECT id FROM employees WHERE user_id=?))"]
        params = [int(u["id"]), int(u["id"])]
        if unread_only:
            conds.append("n.is_read=0")

        q = "SELECT n.* FROM notifications n WHERE " + " AND ".join(conds) + " ORDER BY datetime(n.created_at) DESC, n.id DESC LIMIT ?"
        params.append(limit)
        rows = [dict(r) for r in db.execute(q, params).fetchall()]
        return jsonify({"ok": True, "rows": rows})

    if request.method == "PATCH":
        data = request.get_json(force=True, silent=True) or {}
        nid = data.get("id") or request.args.get("id", type=int)
        mark_all = str(data.get("all") or request.args.get("all") or "").strip() in ("1", "true", "yes")

        try:
            if mark_all:
                db.execute(
                    "UPDATE notifications SET is_read=1 WHERE (user_id=? OR employee_id IN (SELECT id FROM employees WHERE user_id=?))",
                    (int(u["id"]), int(u["id"])),
                )
                db.commit()
                return jsonify({"ok": True})
            if not nid:
                return jsonify({"ok": False, "error": "missing_id"}), 400
            db.execute(
                "UPDATE notifications SET is_read=1 WHERE id=? AND (user_id=? OR employee_id IN (SELECT id FROM employees WHERE user_id=?))",
                (int(nid), int(u["id"]), int(u["id"])),
            )
            db.commit()
            return jsonify({"ok": True})
        except Exception as e:
            db.rollback()
            return jsonify({"ok": False, "error": str(e)}), 500

    # DELETE
    data = request.get_json(force=True, silent=True) or {}
    nid = data.get("id") or request.args.get("id", type=int)
    delete_all = str(data.get("all") or request.args.get("all") or "").strip() in ("1", "true", "yes")

    # For safety: allow deleting all only for owner.
    if delete_all and normalize_role(u.get("role")) not in ("owner", "admin"):
        return jsonify({"ok": False, "error": "forbidden"}), 403
    try:
        if delete_all:
            db.execute(
                "DELETE FROM notifications WHERE (user_id=? OR employee_id IN (SELECT id FROM employees WHERE user_id=?))",
                (int(u["id"]), int(u["id"])),
            )
            db.commit()
            return jsonify({"ok": True})
        if not nid:
            return jsonify({"ok": False, "error": "missing_id"}), 400
        db.execute(
            "DELETE FROM notifications WHERE id=? AND (user_id=? OR employee_id IN (SELECT id FROM employees WHERE user_id=?))",
            (int(nid), int(u["id"]), int(u["id"])),
        )
        db.commit()
        return jsonify({"ok": True})
    except Exception as e:
        db.rollback()
        return jsonify({"ok": False, "error": str(e)}), 500
