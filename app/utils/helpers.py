# Green David App
import json
import re
from datetime import datetime
from app.database import get_db
from app.utils.permissions import current_user


def audit_event(user_id, action: str, entity_type: str, entity_id=None, before=None, after=None, meta=None):
    """Write a single audit log entry. Never raises (to avoid breaking user flows)."""
    try:
        db = get_db()
        db.execute(
            "INSERT INTO audit_log(user_id, action, entity_type, entity_id, before_json, after_json, meta_json) VALUES (?,?,?,?,?,?,?)",
            (
                user_id,
                action,
                entity_type,
                entity_id,
                json.dumps(before, ensure_ascii=False) if before is not None else None,
                json.dumps(after, ensure_ascii=False) if after is not None else None,
                json.dumps(meta, ensure_ascii=False) if meta is not None else None,
            ),
        )
        db.commit()
    except Exception:
        pass


def _employee_user_id(db, employee_id: int):
    """Return linked user_id for an employee, or None."""
    try:
        r = db.execute("SELECT user_id FROM employees WHERE id=?", (int(employee_id),)).fetchone()
        return int(r[0]) if r and r[0] is not None else None
    except Exception:
        return None


def create_notification(*, user_id=None, employee_id=None, kind="info", title="", body="", entity_type=None, entity_id=None):
    """Create an in-app notification. Never raises."""
    try:
        db = get_db()
        if employee_id is not None and user_id is None:
            user_id = _employee_user_id(db, int(employee_id))
        db.execute(
            "INSERT INTO notifications(user_id, employee_id, kind, title, body, entity_type, entity_id) VALUES (?,?,?,?,?,?,?)",
            (
                int(user_id) if user_id is not None else None,
                int(employee_id) if employee_id is not None else None,
                str(kind or "info"),
                str(title or ""),
                str(body or ""),
                str(entity_type) if entity_type is not None else None,
                int(entity_id) if entity_id is not None else None,
            ),
        )
        db.commit()
    except Exception:
        pass


def _expand_assignees_with_delegate(db, employee_ids):
    """Expand assignees by adding one-hop delegates.

    Returns: (expanded_ids, delegations)
      - expanded_ids: list[int]
      - delegations: list[{'from': int, 'to': int}]

    Note: intentionally non-recursive to avoid cycles and surprises.
    """
    try:
        ids = [int(x) for x in (employee_ids or []) if str(x).strip()]
    except Exception:
        ids = []
    seen = set(ids)
    delegations = []

    for eid in list(ids):
        try:
            r = db.execute(
                "SELECT delegate_employee_id FROM employees WHERE id=?",
                (int(eid),),
            ).fetchone()
            did = int(r[0]) if r and r[0] is not None else None
        except Exception:
            did = None

        if did and did != eid and did not in seen:
            ids.append(did)
            seen.add(did)
            delegations.append({"from": int(eid), "to": int(did)})

    return ids, delegations


def _notify_assignees(entity_type: str, entity_id: int, assignee_ids, title: str, body: str, actor_user_id=None):
    """Notify assignees (employees) - skips actor if mapped to same employee user."""
    db = get_db()
    # Map actor user_id -> employee_id (best-effort)
    actor_employee_id = None
    try:
        if actor_user_id:
            r = db.execute("SELECT id FROM employees WHERE user_id=?", (int(actor_user_id),)).fetchone()
            actor_employee_id = int(r[0]) if r else None
    except Exception:
        actor_employee_id = None

    for eid in assignee_ids or []:
        try:
            eid = int(eid)
        except Exception:
            continue
        if actor_employee_id and eid == actor_employee_id:
            continue
        create_notification(
            employee_id=eid,
            kind="assignment",
            title=title,
            body=body,
            entity_type=entity_type,
            entity_id=int(entity_id),
        )


def _normalize_date(v):
    if not v:
        return v
    s = str(v).strip()
    m = re.match(r"^(\d{4})-(\d{1,2})-(\d{1,2})$", s)
    if m:
        y, M, d = m.groups()
        return f"{int(y):04d}-{int(M):02d}-{int(d):02d}"
    m = re.match(r"^(\d{1,2})[\.\s-](\d{1,2})[\.\s-](\d{4})$", s)
    if m:
        d, M, y = m.groups()
        return f"{int(y):04d}-{int(M):02d}-{int(d):02d}"
    return s


def _jobs_info():
    rows = get_db().execute("PRAGMA table_info(jobs)").fetchall()
    # rows: cid, name, type, notnull, dflt_value, pk
    return {r[1]: {"notnull": int(r[3])} for r in rows}


def _job_title_col():
    info = _jobs_info()
    if "title" in info:
        return "title"
    return "name" if "name" in info else "title"


def _job_select_all():
    info = _jobs_info()
    base_cols = "id, client, status, city, code, date, note"
    date_cols = ", created_date, start_date" if "created_date" in info else ""
    deadline_col = ", deadline" if "deadline" in info else ""
    address_col = ", address" if "address" in info else ""
    progress_col = ", progress" if "progress" in info else ""
    time_col = ", time_spent_minutes" if "time_spent_minutes" in info else ""
    budget_col = ", budget" if "budget" in info else ""
    cost_col = ", cost_spent" if "cost_spent" in info else ", actual_cost" if "actual_cost" in info else ""
    party_col = ", party_id" if "party_id" in info else ""
    if "title" in info:
        return f"SELECT title, {base_cols}{date_cols}{deadline_col}{address_col}{progress_col}{time_col}{budget_col}{cost_col}{party_col} FROM jobs"
    if "name" in info:
        return f"SELECT name AS title, {base_cols}{date_cols}{deadline_col}{address_col}{progress_col}{time_col}{budget_col}{cost_col}{party_col} FROM jobs"
    return f"SELECT '' AS title, {base_cols}{date_cols}{deadline_col}{address_col}{progress_col}{time_col}{budget_col}{cost_col}{party_col} FROM jobs"


def _job_insert_cols_and_vals(title, client, status, city, code, dt, note, owner_id=None, party_id=None):
    info = _jobs_info()
    cols = []
    vals = []
    # Keep legacy 'name' in sync if present
    if "title" in info:
        cols.append("title"); vals.append(title)
    if "name" in info:
        cols.append("name"); vals.append(title)
    cols += ["client","status","city","code","date","note"]
    vals += [client, status, city, code, dt, note]
    # party_id pokud existuje
    if "party_id" in info and party_id is not None:
        cols.append("party_id"); vals.append(int(party_id))
    # legacy NOT NULL columns without defaults
    now = datetime.utcnow().isoformat()
    if "created_at" in info:
        cols.append("created_at"); vals.append(now)
    if "updated_at" in info:
        cols.append("updated_at"); vals.append(now)
    # legacy owner_id
    if "owner_id" in info:
        if owner_id is None:
            cu = current_user()
            owner_id = cu["id"] if cu else None
        cols.append("owner_id"); vals.append(int(owner_id) if owner_id is not None else None)
    return cols, vals


def _job_title_update_set(params_list, title_value):
    info = _jobs_info()
    sets = []
    if "title" in info:
        sets.append("title=?"); params_list.append(title_value)
    if "name" in info:
        sets.append("name=?"); params_list.append(title_value)
    return sets
