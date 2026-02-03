# Task and Issue Assignment Helpers
# Multi-employee assignment support

def assign_employees_to_task(db, task_id, employee_ids, primary_employee_id=None):
    """
    Přiřadí více zaměstnanců k úkolu
    
    Args:
        db: Database connection
        task_id: ID úkolu
        employee_ids: List of employee IDs to assign
        primary_employee_id: ID primárního odpovědného (volitelné)
    """
    if not employee_ids:
        return
    
    # Smaž staré přiřazení
    db.execute("DELETE FROM task_assignments WHERE task_id = ?", (task_id,))
    
    # Přidej nová přiřazení
    for emp_id in employee_ids:
        is_primary = 1 if emp_id == primary_employee_id else 0
        db.execute("""
            INSERT INTO task_assignments (task_id, employee_id, is_primary)
            VALUES (?, ?, ?)
        """, (task_id, emp_id, is_primary))

def assign_employees_to_issue(db, issue_id, employee_ids, primary_employee_id=None):
    """
    Přiřadí více zaměstnanců k issue
    
    Args:
        db: Database connection
        issue_id: ID issue
        employee_ids: List of employee IDs to assign
        primary_employee_id: ID primárního odpovědného (volitelné)
    """
    if not employee_ids:
        return
    
    # Smaž staré přiřazení
    db.execute("DELETE FROM issue_assignments WHERE issue_id = ?", (issue_id,))
    
    # Přidej nová přiřazení
    for emp_id in employee_ids:
        is_primary = 1 if emp_id == primary_employee_id else 0
        db.execute("""
            INSERT INTO issue_assignments (issue_id, employee_id, is_primary)
            VALUES (?, ?, ?)
        """, (issue_id, emp_id, is_primary))

def get_task_assignees(db, task_id):
    """Vrátí seznam přiřazených zaměstnanců pro úkol"""
    rows = db.execute("""
        SELECT e.id, e.name, ta.is_primary
        FROM task_assignments ta
        JOIN employees e ON e.id = ta.employee_id
        WHERE ta.task_id = ?
        ORDER BY ta.is_primary DESC, e.name ASC
    """, (task_id,)).fetchall()
    
    return [{"id": r["id"], "name": r["name"], "is_primary": bool(r["is_primary"])} for r in rows]

def get_issue_assignees(db, issue_id):
    """Vrátí seznam přiřazených zaměstnanců pro issue"""
    rows = db.execute("""
        SELECT e.id, e.name, ia.is_primary
        FROM issue_assignments ia
        JOIN employees e ON e.id = ia.employee_id
        WHERE ia.issue_id = ?
        ORDER BY ia.is_primary DESC, e.name ASC
    """, (issue_id,)).fetchall()
    
    return [{"id": r["id"], "name": r["name"], "is_primary": bool(r["is_primary"])} for r in rows]

def get_employee_tasks(db, employee_id):
    """Vrátí všechny úkoly přiřazené zaměstnanci (přes assignments)"""
    rows = db.execute("""
        SELECT DISTINCT t.*, j.name as job_name, ta.is_primary
        FROM tasks t
        JOIN task_assignments ta ON ta.task_id = t.id
        LEFT JOIN jobs j ON j.id = t.job_id
        WHERE ta.employee_id = ?
        ORDER BY t.due_date ASC, t.id DESC
    """, (employee_id,)).fetchall()
    
    return [dict(r) for r in rows]

def get_employee_issues(db, employee_id):
    """Vrátí všechny issues přiřazené zaměstnanci (přes assignments)"""
    rows = db.execute("""
        SELECT DISTINCT i.*, j.name as job_name, ia.is_primary
        FROM issues i
        JOIN issue_assignments ia ON ia.issue_id = i.id
        LEFT JOIN jobs j ON j.id = i.job_id
        WHERE ia.employee_id = ?
        ORDER BY 
            CASE i.status 
                WHEN 'open' THEN 0 
                WHEN 'in_progress' THEN 1 
                ELSE 2 
            END,
            i.created_at DESC
    """, (employee_id,)).fetchall()
    
    return [dict(r) for r in rows]
