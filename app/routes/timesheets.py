# Green David App
from flask import Blueprint, jsonify, request, send_from_directory, render_template
from datetime import datetime, timedelta, date
from app.database import get_db
from app.utils.permissions import require_auth, require_role, requires_role, get_current_user
from app.utils.helpers import audit_event, _normalize_date

timesheets_bp = Blueprint('timesheets', __name__)


@timesheets_bp.route("/timesheets.html")
def timesheets_html():
    return render_template("timesheets.html", page_title="Výkazy")


# Timesheets routes from main.py
@timesheets_bp.route("/api/timesheets/<int:timesheet_id>/approve", methods=["POST"])
@requires_role('owner', 'admin', 'manager', 'lander')
def api_approve_timesheet(timesheet_id):
    """Schválení výkazu - jen pro nadřízené"""
    user = get_current_user()
    if not user:
        return jsonify({"ok": False, "error": "unauthorized"}), 401
    
    db = get_db()
    
    # Získat timesheet
    timesheet = db.execute(
        "SELECT employee_id FROM timesheets WHERE id = ?",
        (timesheet_id,)
    ).fetchone()
    
    if not timesheet:
        return jsonify({"ok": False, "error": "not_found"}), 404
    
    # Kontrola oprávnění - owner může všechno
    if user['role'] not in ('owner', 'admin'):
        # Pro ostatní role potřebujeme zkontrolovat hierarchii
        # Pokud timesheets nemá přímý link na users, použijeme employees
        # Prozatím povolíme všem nadřízeným
        pass
    
    # Zkontrolovat, zda timesheets tabulka má sloupce pro schválení
    cols = [r[1] for r in db.execute("PRAGMA table_info(timesheets)").fetchall()]
    
    if 'approved' not in cols:
        db.execute("ALTER TABLE timesheets ADD COLUMN approved INTEGER DEFAULT 0")
        db.execute("ALTER TABLE timesheets ADD COLUMN approved_by INTEGER NULL")
        db.execute("ALTER TABLE timesheets ADD COLUMN approved_at TEXT NULL")
        db.commit()
    
    # Schválit
    try:
        db.execute(
            "UPDATE timesheets SET approved = 1, approved_by = ?, approved_at = datetime('now') WHERE id = ?",
            (user['id'], timesheet_id)
        )
        db.commit()
        return jsonify({"ok": True})
    except Exception as e:
        db.rollback()
        return jsonify({"ok": False, "error": str(e)}), 500

# ✅ jobs with legacy schema compatibility
@timesheets_bp.route("/api/timesheets", methods=["GET","POST","PATCH","DELETE"])
def api_timesheets():
    u, err = require_role(write=(request.method!="GET"))
    if err: return err
    db = get_db()

    if request.method == "GET":
        emp = request.args.get("employee_id", type=int)
        jid = request.args.get("job_id", type=int)
        task_id = request.args.get("task_id", type=int)
        d_from = _normalize_date(request.args.get("from"))
        d_to   = _normalize_date(request.args.get("to"))
        title_col = _job_title_col()
        
        # Zkontroluj existující sloupce
        timesheet_cols = [r[1] for r in db.execute("PRAGMA table_info(timesheets)").fetchall()]
        
        # Sestav SELECT s novými sloupci
        base_cols = "t.id,t.employee_id,t.job_id,t.date,t.hours,t.place,t.activity"
        new_cols = []
        
        if 'duration_minutes' in timesheet_cols:
            new_cols.append("COALESCE(t.duration_minutes, CAST(t.hours * 60 AS INTEGER)) AS duration_minutes")
        if 'labor_cost' in timesheet_cols:
            new_cols.append("COALESCE(t.labor_cost, 0) AS labor_cost")
        if 'work_type' in timesheet_cols:
            new_cols.append("t.work_type")
        if 'start_time' in timesheet_cols:
            new_cols.append("t.start_time")
        if 'end_time' in timesheet_cols:
            new_cols.append("t.end_time")
        if 'location' in timesheet_cols:
            new_cols.append("COALESCE(t.location, t.place) AS location")
        if 'task_id' in timesheet_cols:
            new_cols.append("t.task_id")
        if 'material_used' in timesheet_cols:
            new_cols.append("t.material_used")
        if 'weather_snapshot' in timesheet_cols:
            new_cols.append("t.weather_snapshot")
        if 'performance_signal' in timesheet_cols:
            new_cols.append("t.performance_signal")
        if 'delay_reason' in timesheet_cols:
            new_cols.append("t.delay_reason")
        if 'delay_note' in timesheet_cols:
            new_cols.append("t.delay_note")
        if 'photo_url' in timesheet_cols:
            new_cols.append("t.photo_url")
        if 'note' in timesheet_cols:
            new_cols.append("COALESCE(t.note, t.activity) AS note")
        if 'ai_flags' in timesheet_cols:
            new_cols.append("t.ai_flags")
        if 'created_at' in timesheet_cols:
            new_cols.append("t.created_at")
        
        all_cols = base_cols
        if new_cols:
            all_cols += "," + ",".join(new_cols)
        
        q = f"""SELECT {all_cols},
                      e.name AS employee_name, j.{title_col} AS job_title, j.code AS job_code
               FROM timesheets t
               LEFT JOIN employees e ON e.id=t.employee_id
               LEFT JOIN jobs j ON j.id=t.job_id"""
        conds=[]; params=[]
        if emp: conds.append("t.employee_id=?"); params.append(emp)
        if jid: conds.append("t.job_id=?"); params.append(jid)
        if task_id: conds.append("t.task_id=?"); params.append(task_id)
        if d_from and d_to:
            conds.append("date(t.date) BETWEEN date(?) AND date(?)"); params.extend([d_from, d_to])
        elif d_from:
            conds.append("date(t.date) >= date(?)"); params.append(d_from)
        elif d_to:
            conds.append("date(t.date) <= date(?)"); params.append(d_to)
        if conds: q += " WHERE " + " AND ".join(conds)
        q += " ORDER BY t.date ASC, t.id ASC"
        rows = db.execute(q, params).fetchall()
        
        # Parsuj JSON sloupce
        import json as json_lib
        result_rows = []
        for r in rows:
            row_dict = dict(r)
            # Parsuj JSON sloupce
            for json_col in ['material_used', 'weather_snapshot', 'ai_flags']:
                if json_col in row_dict and row_dict[json_col]:
                    try:
                        row_dict[json_col] = json_lib.loads(row_dict[json_col])
                    except:
                        row_dict[json_col] = None
            result_rows.append(row_dict)
        
        return jsonify({"ok": True, "rows": result_rows})

    if request.method == "POST":
        try:
            import json as json_lib
            data = request.get_json(force=True, silent=True) or {}
            emp = data.get("employee_id")
            job = data.get("job_id")  # Může být None nebo 0
            dt = data.get("date")
            hours = data.get("hours")
            duration_minutes = data.get("duration_minutes")
            
            # Validace povinných polí
            if not emp or not dt:
                return jsonify({"ok": False, "error": "missing_required_fields"}), 400
            
            # job_id může být None/0 pro výkazy bez zakázky
            if job is None:
                job = 0
            
            # Vypočti duration_minutes z hours pokud není zadáno
            if duration_minutes is None:
                if hours is not None:
                    duration_minutes = int(float(hours) * 60)
                else:
                    duration_minutes = 480  # default 8h
            
            # Vypočti hours z duration_minutes pokud není zadáno
            if hours is None:
                hours = duration_minutes / 60.0
            
            # Stará pole (zpětná kompatibilita)
            place = data.get("place") or data.get("location") or ""
            activity = data.get("activity") or data.get("note") or ""
            
            # Nová pole
            user_id = data.get("user_id")
            work_type = data.get("work_type") or "manual"
            start_time = data.get("start_time")
            end_time = data.get("end_time")
            location = data.get("location") or place
            task_id = data.get("task_id")
            material_used = json_lib.dumps(data.get("material_used")) if data.get("material_used") else None
            weather_snapshot = json_lib.dumps(data.get("weather_snapshot")) if data.get("weather_snapshot") else None
            performance_signal = data.get("performance_signal") or "normal"
            delay_reason = data.get("delay_reason")
            delay_note = data.get("delay_note")
            photo_url = data.get("photo_url")
            note = data.get("note") or activity
            
            # Vypočti labor_cost
            labor_cost = calculate_labor_cost(int(emp), int(job) if job else None, duration_minutes, db)
            
            # Detekuj anomálie
            ai_flags_data = detect_anomalies({
                'duration_minutes': duration_minutes,
                'performance_signal': performance_signal,
                'delay_reason': delay_reason
            }, db)
            ai_flags = json_lib.dumps(ai_flags_data)
            
            # Vložení do DB
            cols = ["employee_id", "job_id", "date", "hours", "duration_minutes", "place", "activity"]
            vals = [int(emp), int(job), _normalize_date(dt), float(hours), duration_minutes, place, activity]
            
            # Přidej nová pole pokud existují sloupce
            timesheet_cols = [r[1] for r in db.execute("PRAGMA table_info(timesheets)").fetchall()]
            
            if 'user_id' in timesheet_cols:
                cols.append("user_id"); vals.append(int(user_id) if user_id else None)
            if 'work_type' in timesheet_cols:
                cols.append("work_type"); vals.append(work_type)
            if 'start_time' in timesheet_cols:
                cols.append("start_time"); vals.append(start_time)
            if 'end_time' in timesheet_cols:
                cols.append("end_time"); vals.append(end_time)
            if 'location' in timesheet_cols:
                cols.append("location"); vals.append(location)
            if 'task_id' in timesheet_cols:
                cols.append("task_id"); vals.append(int(task_id) if task_id else None)
            if 'material_used' in timesheet_cols:
                cols.append("material_used"); vals.append(material_used)
            if 'weather_snapshot' in timesheet_cols:
                cols.append("weather_snapshot"); vals.append(weather_snapshot)
            if 'performance_signal' in timesheet_cols:
                cols.append("performance_signal"); vals.append(performance_signal)
            if 'delay_reason' in timesheet_cols:
                cols.append("delay_reason"); vals.append(delay_reason)
            if 'delay_note' in timesheet_cols:
                cols.append("delay_note"); vals.append(delay_note)
            if 'photo_url' in timesheet_cols:
                cols.append("photo_url"); vals.append(photo_url)
            if 'note' in timesheet_cols:
                cols.append("note"); vals.append(note)
            if 'ai_flags' in timesheet_cols:
                cols.append("ai_flags"); vals.append(ai_flags)
            if 'labor_cost' in timesheet_cols:
                cols.append("labor_cost"); vals.append(labor_cost)
            
            placeholders = ",".join("?" * len(vals))
            db.execute(f"INSERT INTO timesheets({','.join(cols)}) VALUES ({placeholders})", vals)
            db.commit()
            
            # Získat ID nového výkazu
            new_id = db.execute("SELECT last_insert_rowid()").fetchone()[0]
            
            # Zpracuj materiál
            if material_used:
                process_material_usage(new_id, data.get("material_used"), None, db)
            
            # Přepočti statistiky zakázky
            if job:
                recalculate_job_stats(int(job), db)
            
            print(f"✓ Timesheet {new_id} created successfully (emp:{emp}, job:{job}, date:{dt})")
            return jsonify({"ok": True, "id": new_id})
        except Exception as e:
            db.rollback()
            print(f"✗ Error creating timesheet: {e}")
            import traceback
            traceback.print_exc()
            return jsonify({"ok": False, "error": str(e)}), 500

    if request.method == "PATCH":
        try:
            import json as json_lib
            data = request.get_json(force=True, silent=True) or {}
            tid = data.get("id")
            if not tid:
                return jsonify({"ok": False, "error": "missing_id"}), 400
            
            # Získej starý výkaz pro delta materiálu
            old_row = db.execute("SELECT job_id, material_used FROM timesheets WHERE id=?", (tid,)).fetchone()
            old_job_id = old_row[0] if old_row else None
            old_material = old_row[1] if old_row and old_row[1] else None
            
            # Získej existující sloupce
            timesheet_cols = [r[1] for r in db.execute("PRAGMA table_info(timesheets)").fetchall()]
            
            # Povolená pole (stará + nová)
            allowed = ["employee_id", "job_id", "date", "hours", "duration_minutes", "place", "activity",
                      "location", "note", "work_type", "start_time", "end_time", "task_id",
                      "material_used", "weather_snapshot", "performance_signal", "delay_reason",
                      "delay_note", "photo_url"]
            
            sets, vals = [], []
            
            # Zpracuj každé pole
            for k in allowed:
                if k not in data:
                    continue
                
                # Zkontroluj existenci sloupce
                if k not in timesheet_cols and k not in ["hours", "place", "activity"]:
                    continue
                
                v = data[k]
                
                # Speciální zpracování podle typu
                if k == "date":
                    v = _normalize_date(v)
                elif k in ("employee_id", "job_id", "task_id"):
                    v = int(v) if v else None
                elif k == "hours":
                    v = float(v) if v is not None else None
                elif k == "duration_minutes":
                    v = int(v) if v is not None else None
                elif k in ("material_used", "weather_snapshot", "ai_flags"):
                    v = json_lib.dumps(v) if v else None
                
                sets.append(f"{k}=?"); vals.append(v)
            
            # Přepočti duration_minutes z hours nebo naopak
            if "hours" in data and "duration_minutes" not in data:
                hours_val = float(data["hours"]) if data["hours"] is not None else None
                if hours_val is not None and "duration_minutes" in timesheet_cols:
                    sets.append("duration_minutes=?"); vals.append(int(hours_val * 60))
            elif "duration_minutes" in data and "hours" not in data:
                mins_val = int(data["duration_minutes"]) if data["duration_minutes"] is not None else None
                if mins_val is not None:
                    sets.append("hours=?"); vals.append(mins_val / 60.0)
            
            # Přepočti labor_cost pokud se změnily relevantní hodnoty
            if any(k in data for k in ["employee_id", "job_id", "duration_minutes", "hours"]):
                emp = data.get("employee_id")
                job = data.get("job_id")
                duration = data.get("duration_minutes")
                
                if not emp:
                    old_emp = db.execute("SELECT employee_id FROM timesheets WHERE id=?", (tid,)).fetchone()
                    emp = old_emp[0] if old_emp else None
                
                if not job and old_job_id:
                    job = old_job_id
                
                if not duration:
                    old_dur = db.execute("SELECT duration_minutes, hours FROM timesheets WHERE id=?", (tid,)).fetchone()
                    if old_dur:
                        duration = old_dur[0] if old_dur[0] else int(old_dur[1] * 60) if old_dur[1] else 480
                
                if emp and duration and "labor_cost" in timesheet_cols:
                    labor_cost = calculate_labor_cost(int(emp), int(job) if job else None, duration, db)
                    sets.append("labor_cost=?"); vals.append(labor_cost)
            
            # Aktualizuj AI flags
            if any(k in data for k in ["duration_minutes", "hours", "performance_signal", "delay_reason"]):
                old_row = db.execute(
                    "SELECT duration_minutes, hours, performance_signal, delay_reason FROM timesheets WHERE id=?",
                    (tid,)
                ).fetchone()
                
                duration_for_flags = data.get("duration_minutes") or (old_row[0] if old_row else None) or (int((data.get("hours") or (old_row[1] if old_row else 0)) * 60))
                perf_signal = data.get("performance_signal") or (old_row[2] if old_row else "normal")
                delay_reason = data.get("delay_reason") or (old_row[3] if old_row else None)
                
                if "ai_flags" in timesheet_cols:
                    ai_flags_data = detect_anomalies({
                        'duration_minutes': duration_for_flags,
                        'performance_signal': perf_signal,
                        'delay_reason': delay_reason
                    }, db)
                    sets.append("ai_flags=?"); vals.append(json_lib.dumps(ai_flags_data))
            
            if not sets:
                return jsonify({"ok": False, "error": "no_fields"}), 400
            
            vals.append(int(tid))
            db.execute("UPDATE timesheets SET " + ",".join(sets) + " WHERE id=?", vals)
            db.commit()
            
            # Zpracuj změny materiálu
            if "material_used" in data:
                new_material = data.get("material_used")
                process_material_usage(tid, new_material, old_material, db)
            
            # Přepočti statistiky zakázky (stará i nová)
            new_job_id = data.get("job_id", old_job_id)
            if new_job_id:
                recalculate_job_stats(int(new_job_id), db)
            if old_job_id and old_job_id != new_job_id:
                recalculate_job_stats(int(old_job_id), db)
            
            print(f"✓ Timesheet {tid} updated successfully")
            return jsonify({"ok": True})
        except Exception as e:
            db.rollback()
            print(f"✗ Error updating timesheet: {e}")
            import traceback
            traceback.print_exc()
            return jsonify({"ok": False, "error": str(e)}), 500

    # DELETE
    try:
        tid = request.args.get("id", type=int)
        if not tid:
            return jsonify({"ok": False, "error": "missing_id"}), 400
        
        # Získej data před smazáním pro reverz materiálu
        old_row = db.execute(
            "SELECT job_id, material_used FROM timesheets WHERE id=?",
            (tid,)
        ).fetchone()
        
        old_job_id = old_row[0] if old_row else None
        old_material = old_row[1] if old_row else None
        
        # Vrať materiál do skladu
        if old_material:
            try:
                import json as json_lib
                material_list = json_lib.loads(old_material) if isinstance(old_material, str) else old_material
                if material_list:
                    process_material_usage(tid, [], material_list, db)  # Reverz: odečti zápornou deltu
            except Exception as e:
                print(f"Warning: Could not reverse material usage: {e}")
        
        # Smaž výkaz
        db.execute("DELETE FROM timesheets WHERE id=?", (tid,))
        db.commit()
        
        # Přepočti statistiky zakázky
        if old_job_id:
            recalculate_job_stats(int(old_job_id), db)
        
        print(f"✓ Timesheet {tid} deleted successfully")
        return jsonify({"ok": True})
    except Exception as e:
        db.rollback()
        print(f"✗ Error deleting timesheet: {e}")
        return jsonify({"ok": False, "error": str(e)}), 500

# ----------------- Worklog Service Layer -----------------
@timesheets_bp.route("/api/timesheets/summary", methods=["GET"])
def api_timesheets_summary():
    """Agregační endpoint pro souhrnné statistiky"""
    u, err = require_role(write=False)
    if err:
        return err
    
    db = get_db()
    emp = request.args.get("employee_id", type=int)
    jid = request.args.get("job_id", type=int)
    d_from = _normalize_date(request.args.get("from"))
    d_to = _normalize_date(request.args.get("to"))
    
    # Build WHERE conditions
    conds = []
    params = []
    if emp:
        conds.append("t.employee_id=?")
        params.append(emp)
    if jid:
        conds.append("t.job_id=?")
        params.append(jid)
    if d_from and d_to:
        conds.append("date(t.date) BETWEEN date(?) AND date(?)")
        params.extend([d_from, d_to])
    elif d_from:
        conds.append("date(t.date) >= date(?)")
        params.append(d_from)
    elif d_to:
        conds.append("date(t.date) <= date(?)")
        params.append(d_to)
    
    where_clause = " WHERE " + " AND ".join(conds) if conds else ""
    
    # Zkontroluj existující sloupce
    timesheet_cols = [r[1] for r in db.execute("PRAGMA table_info(timesheets)").fetchall()]
    duration_col = "COALESCE(t.duration_minutes, CAST(t.hours * 60 AS INTEGER))" if 'duration_minutes' in timesheet_cols else "CAST(t.hours * 60 AS INTEGER)"
    
    # Celkem minut a hodin
    total_result = db.execute(
        f"SELECT SUM({duration_col}) as total_minutes, COUNT(DISTINCT t.date) as work_days FROM timesheets t {where_clause}",
        params
    ).fetchone()
    
    total_minutes = int(total_result[0] or 0)
    total_hours = total_minutes / 60.0
    work_days = int(total_result[1] or 0)
    avg_per_day = (total_hours / work_days) if work_days > 0 else 0
    
    # Overtime (>8h denně)
    overtime_result = db.execute(
        f"""SELECT SUM(CASE WHEN {duration_col} > 480 THEN {duration_col} - 480 ELSE 0 END) as overtime_minutes
            FROM timesheets t {where_clause}""",
        params
    ).fetchone()
    overtime_minutes = int(overtime_result[0] or 0)
    
    # Top jobs
    title_col = _job_title_col()
    top_jobs = db.execute(
        f"""SELECT t.job_id, j.{title_col} as job_name, SUM({duration_col}) as minutes
            FROM timesheets t
            LEFT JOIN jobs j ON j.id = t.job_id
            {where_clause}
            GROUP BY t.job_id, j.{title_col}
            ORDER BY minutes DESC
            LIMIT 10""",
        params
    ).fetchall()
    
    # Top work types
    top_work_types = []
    if 'work_type' in timesheet_cols:
        top_work_types = db.execute(
            f"""SELECT work_type, SUM({duration_col}) as minutes
                FROM timesheets t
                {where_clause}
                GROUP BY work_type
                ORDER BY minutes DESC""",
            params
        ).fetchall()
    
    # Anomálie count
    anomalies_count = 0
    if 'ai_flags' in timesheet_cols:
        import json as json_lib
        all_flags = db.execute(
            f"SELECT ai_flags FROM timesheets t {where_clause}",
            params
        ).fetchall()
        for flag_row in all_flags:
            if flag_row[0]:
                try:
                    flags = json_lib.loads(flag_row[0])
                    if flags.get('anomaly'):
                        anomalies_count += 1
                except:
                    pass
    
    return jsonify({
        "ok": True,
        "total_minutes": total_minutes,
        "total_hours": round(total_hours, 2),
        "avg_per_day": round(avg_per_day, 2),
        "overtime_minutes": overtime_minutes,
        "work_days": work_days,
        "top_jobs": [{"job_id": r[0], "job_name": r[1] or f"Projekt {r[0]}", "minutes": int(r[2] or 0)} for r in top_jobs],
        "top_work_types": [{"work_type": r[0] or "manual", "minutes": int(r[1] or 0)} for r in top_work_types],
        "anomalies_count": anomalies_count
    })

@timesheets_bp.route("/api/timesheets/heatmap", methods=["GET"])
def api_timesheets_heatmap():
    """Heatmapa dat pro vizualizaci týdenního zatížení"""
    u, err = require_role(write=False)
    if err:
        return err
    
    db = get_db()
    emp = request.args.get("employee_id", type=int)
    d_from = _normalize_date(request.args.get("from"))
    d_to = _normalize_date(request.args.get("to"))
    
    if not d_from or not d_to:
        return jsonify({"ok": False, "error": "from and to dates required"}), 400
    
    conds = ["date(t.date) BETWEEN date(?) AND date(?)"]
    params = [d_from, d_to]
    
    if emp:
        conds.append("t.employee_id=?")
        params.append(emp)
    
    where_clause = " WHERE " + " AND ".join(conds)
    
    # Zkontroluj existující sloupce
    timesheet_cols = [r[1] for r in db.execute("PRAGMA table_info(timesheets)").fetchall()]
    duration_col = "COALESCE(t.duration_minutes, CAST(t.hours * 60 AS INTEGER))" if 'duration_minutes' in timesheet_cols else "CAST(t.hours * 60 AS INTEGER)"
    
    # Agregace po dnech
    days_data = db.execute(
        f"""SELECT t.date, SUM({duration_col}) as total_minutes,
                   COUNT(*) as entries_count
            FROM timesheets t
            {where_clause}
            GROUP BY t.date
            ORDER BY t.date""",
        params
    ).fetchall()
    
    import json as json_lib
    
    days = []
    for row in days_data:
        date_str = row[0]
        total_mins = int(row[1] or 0)
        
        # Load level: 0=<4h, 1=4-6h, 2=6-8h, 3=>8h
        load_level = 0
        if total_mins >= 480:  # >=8h
            load_level = 3
        elif total_mins >= 360:  # >=6h
            load_level = 2
        elif total_mins >= 240:  # >=4h
            load_level = 1
        
        # Zkontroluj AI flags pro tento den
        day_flags = {"overtime": total_mins > 480, "anomaly": False}
        if 'ai_flags' in timesheet_cols:
            day_entries = db.execute(
                "SELECT ai_flags FROM timesheets WHERE date = ?" + (" AND employee_id = ?" if emp else ""),
                [date_str] + ([emp] if emp else [])
            ).fetchall()
            for flag_row in day_entries:
                if flag_row[0]:
                    try:
                        flags = json_lib.loads(flag_row[0])
                        if flags.get('anomaly'):
                            day_flags["anomaly"] = True
                            break
                    except:
                        pass
        
        days.append({
            "date": date_str,
            "total_minutes": total_mins,
            "load_level": load_level,
            "flags": day_flags
        })
    
    return jsonify({"ok": True, "days": days})

@timesheets_bp.route("/api/timesheets/ai-insights", methods=["GET"])
def api_timesheets_ai_insights():
    """AI signály a doporučení"""
    u, err = require_role(write=False)
    if err:
        return err
    
    db = get_db()
    d_from = _normalize_date(request.args.get("from"))
    d_to = _normalize_date(request.args.get("to"))
    
    if not d_from or not d_to:
        # Default: poslední týden
        from datetime import datetime, timedelta
        d_to = datetime.now().strftime('%Y-%m-%d')
        d_from = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
    
    where_clause = " WHERE date(t.date) BETWEEN date(?) AND date(?)"
    params = [d_from, d_to]
    
    timesheet_cols = [r[1] for r in db.execute("PRAGMA table_info(timesheets)").fetchall()]
    duration_col = "COALESCE(t.duration_minutes, CAST(t.hours * 60 AS INTEGER))" if 'duration_minutes' in timesheet_cols else "CAST(t.hours * 60 AS INTEGER)"
    
    import json as json_lib
    
    # Workload risk (průměrné denní zatížení)
    workload_data = db.execute(
        f"""SELECT AVG({duration_col}) as avg_daily, COUNT(DISTINCT t.date) as days
            FROM timesheets t {where_clause}""",
        params
    ).fetchone()
    
    avg_daily = float(workload_data[0] or 0) / 60.0  # v hodinách
    workload_risk = min(100, int((avg_daily / 8.0) * 100))  # 0-100 skóre
    
    # Slowdown jobs (zakázky s rostoucím časem bez progressu)
    title_col = _job_title_col()
    slowdown_jobs = []
    if 'work_type' in timesheet_cols and 'performance_signal' in timesheet_cols:
        problem_jobs = db.execute(
            f"""SELECT t.job_id, j.{title_col} as job_name, COUNT(*) as problem_count
                FROM timesheets t
                LEFT JOIN jobs j ON j.id = t.job_id
                {where_clause}
                AND (t.performance_signal IN ('slow', 'problem') OR t.delay_reason IS NOT NULL)
                GROUP BY t.job_id, j.{title_col}
                HAVING problem_count >= 2
                ORDER BY problem_count DESC
                LIMIT 5""",
            params
        ).fetchall()
        
        slowdown_jobs = [
            {
                "job_id": r[0],
                "job_name": r[1] or f"Projekt {r[0]}",
                "reason": "Rostoucí čas bez progressu"
            }
            for r in problem_jobs
        ]
    
    # Anomaly days
    anomaly_days = []
    if 'ai_flags' in timesheet_cols:
        anomaly_rows = db.execute(
            f"""SELECT DISTINCT t.date, COUNT(*) as count
                FROM timesheets t
                {where_clause}
                AND t.ai_flags IS NOT NULL
                GROUP BY t.date""",
            params
        ).fetchall()
        
        for row in anomaly_rows:
            date_str = row[0]
            flags_data = db.execute(
                "SELECT ai_flags FROM timesheets WHERE date = ? AND ai_flags IS NOT NULL LIMIT 1",
                (date_str,)
            ).fetchone()
            
            if flags_data and flags_data[0]:
                try:
                    flags = json_lib.loads(flags_data[0])
                    if flags.get('anomaly'):
                        reasons = []
                        if flags.get('overtime'):
                            reasons.append("Přesčas")
                        if flags.get('low_performance'):
                            reasons.append("Problémový výkon")
                        anomaly_days.append({
                            "date": date_str,
                            "reason": " + ".join(reasons) if reasons else "Detekována anomálie"
                        })
                except:
                    pass
    
    # Recommendations
    recommendations = []
    if workload_risk > 70:
        recommendations.append("Vysoké vytížení týmu - zvažte redistribuci práce")
    if slowdown_jobs:
        recommendations.append(f"Zkontroluj zakázku '{slowdown_jobs[0]['job_name']}' - riziko skluzu")
    if anomaly_days:
        recommendations.append(f"{len(anomaly_days)} dní s anomáliemi - zkontroluj detaily")
    
    return jsonify({
        "ok": True,
        "workload_risk": workload_risk,
        "slowdown_jobs": slowdown_jobs,
        "anomaly_days": anomaly_days,
        "recommendations": recommendations
    })

@timesheets_bp.route("/api/timesheets/export")
def api_timesheets_export():
    u, err = require_role(write=False)
    if err: return err
    db = get_db()
    emp = request.args.get("employee_id", type=int)
    jid = request.args.get("job_id", type=int)
    d_from = _normalize_date(request.args.get("from"))
    d_to   = _normalize_date(request.args.get("to"))
    title_col = _job_title_col()
    q = f"""SELECT t.id,t.date,t.hours,t.place,t.activity,
                  e.name AS employee_name, e.id AS employee_id,
                  j.{title_col} AS job_title, j.code AS job_code, j.id AS job_id
           FROM timesheets t
           LEFT JOIN employees e ON e.id=t.employee_id
           LEFT JOIN jobs j ON j.id=t.job_id"""
    conds=[]; params=[]
    if emp: conds.append("t.employee_id=?"); params.append(emp)
    if jid: conds.append("t.job_id=?"); params.append(jid)
    if d_from and d_to:
        conds.append("date(t.date) BETWEEN date(?) AND date(?)"); params.extend([d_from, d_to])
    elif d_from:
        conds.append("date(t.date) >= date(?)"); params.append(d_from)
    elif d_to:
        conds.append("date(t.date) <= date(?)"); params.append(d_to)
    if conds: q += " WHERE " + " AND ".join(conds)
    q += " ORDER BY t.date ASC, t.id ASC"
    rows = get_db().execute(q, params).fetchall()

    output = io.StringIO()
    import csv as _csv
    writer = _csv.writer(output)
    writer.writerow(["id","date","employee_id","employee_name","job_id","job_title","job_code","hours","place","activity"])
    for r in rows:
        writer.writerow([r["id"], r["date"], r["employee_id"], r["employee_name"] or "", r["job_id"], r["job_title"] or "", r["job_code"] or "", r["hours"], r["place"] or "", r["activity"] or ""])
    mem = io.BytesIO(output.getvalue().encode("utf-8-sig"))
    mem.seek(0)
    fname = "timesheets.csv"
    return send_file(mem, mimetype="text/csv", as_attachment=True, download_name=fname)


@timesheets_bp.route("/api/timesheets/export-advanced", methods=["GET"])
def api_timesheets_export_advanced():
    """Pokročilý export výkazů s filtry - podporuje PDF, XLSX, CSV"""
    u, err = require_role(write=False)
    if err: return err
    
    # Parametry z query stringu
    export_format = request.args.get("format", "csv").lower()  # csv, xlsx, pdf
    emp_ids = request.args.get("employees", "")  # comma-separated IDs nebo "all"
    jid = request.args.get("job_id", type=int)  # konkrétní zakázka nebo None pro všechny
    d_from = _normalize_date(request.args.get("from"))
    d_to = _normalize_date(request.args.get("to"))
    
    db = get_db()
    title_col = _job_title_col()
    
    # Sestavení SQL dotazu
    q = f"""SELECT t.id, t.date, t.hours, t.place, t.activity,
                  e.name AS employee_name, e.id AS employee_id,
                  j.{title_col} AS job_title, j.code AS job_code, j.id AS job_id
           FROM timesheets t
           LEFT JOIN employees e ON e.id = t.employee_id
           LEFT JOIN jobs j ON j.id = t.job_id"""
    
    conds = []
    params = []
    
    # Filtr zaměstnanců
    if emp_ids and emp_ids != "all":
        emp_list = [int(x.strip()) for x in emp_ids.split(",") if x.strip().isdigit()]
        if emp_list:
            placeholders = ",".join("?" * len(emp_list))
            conds.append(f"t.employee_id IN ({placeholders})")
            params.extend(emp_list)
    
    # Filtr zakázky
    if jid:
        conds.append("t.job_id = ?")
        params.append(jid)
    
    # Filtr data
    if d_from and d_to:
        conds.append("date(t.date) BETWEEN date(?) AND date(?)")
        params.extend([d_from, d_to])
    elif d_from:
        conds.append("date(t.date) >= date(?)")
        params.append(d_from)
    elif d_to:
        conds.append("date(t.date) <= date(?)")
        params.append(d_to)
    
    if conds:
        q += " WHERE " + " AND ".join(conds)
    q += " ORDER BY t.date ASC, t.id ASC"
    
    rows = db.execute(q, params).fetchall()
    
    # Generování exportu podle formátu
    if export_format == "pdf":
        return _generate_pdf_export(rows, d_from, d_to)
    elif export_format == "xlsx":
        return _generate_xlsx_export(rows, d_from, d_to)
    else:  # csv
        return _generate_csv_export(rows, d_from, d_to)


@timesheets_bp.route("/timesheets.html")
def page_timesheets():
    # Render template version (keeps original Timesheets design) while using unified JS header via templates/layout.html
    return render_template("timesheets.html", page_title="Výkazy")
# ----------------- Standalone HTML routes -----------------
def page_employees():
    return send_from_directory(".", "employees.html")

@timesheets_bp.route("/calendar.html")
def page_calendar():
    return send_from_directory(".", "calendar.html")

@timesheets_bp.route("/gd/api/worklogs", methods=["GET", "POST", "PUT", "DELETE"])
def gd_api_worklogs():
    """Extended work logs API with new fields"""
    u, err = require_role(write=(request.method != "GET"))
    if err:
        return err
    db = get_db()
    
    if request.method == "GET":
        # GET: List work logs with filters
        user_id = request.args.get("user_id", type=int)
        job_id = request.args.get("job_id", type=int)
        task_id = request.args.get("task_id", type=int)
        d_from = _normalize_date(request.args.get("from"))
        d_to = _normalize_date(request.args.get("to"))
        
        title_col = _job_title_col()
        q = f"""SELECT 
                    t.id, t.user_id, t.employee_id, t.job_id, t.task_id, t.date,
                    COALESCE(t.duration_minutes, CAST(t.hours * 60 AS INTEGER)) as duration_minutes,
                    t.hours, t.work_type, t.start_time, t.end_time,
                    COALESCE(t.location, t.place) as location, t.place,
                    COALESCE(t.note, t.activity) as note, t.activity,
                    t.material_used, t.weather_snapshot, t.performance_signal,
                    t.delay_reason, t.photo_url, t.ai_flags, t.labor_cost, t.training_id, t.created_at,
                    e.name AS employee_name,
                    j.{title_col} AS job_title, j.code AS job_code
               FROM timesheets t
               LEFT JOIN employees e ON e.id = t.employee_id
               LEFT JOIN jobs j ON j.id = t.job_id"""
        
        conds = []
        params = []
        
        if user_id:
            conds.append("(t.user_id = ? OR (t.user_id IS NULL AND t.employee_id IN (SELECT id FROM employees WHERE user_id = ?)))")
            params.extend([user_id, user_id])
        if job_id:
            conds.append("t.job_id = ?")
            params.append(job_id)
        if task_id:
            conds.append("t.task_id = ?")
            params.append(task_id)
        if d_from and d_to:
            conds.append("date(t.date) BETWEEN date(?) AND date(?)")
            params.extend([d_from, d_to])
        elif d_from:
            conds.append("date(t.date) >= date(?)")
            params.append(d_from)
        elif d_to:
            conds.append("date(t.date) <= date(?)")
            params.append(d_to)
        
        if conds:
            q += " WHERE " + " AND ".join(conds)
        q += " ORDER BY t.date DESC, t.id DESC"
        
        rows = db.execute(q, params).fetchall()
        return jsonify({"ok": True, "worklogs": [dict(r) for r in rows]})
    
    if request.method == "POST":
        # POST: Create new work log
        try:
            data = request.get_json(force=True, silent=True) or {}
            
            # Required fields
            job_id = data.get("job_id")
            date = data.get("date")
            duration_minutes = data.get("duration_minutes")
            work_type = data.get("work_type", "manual")
            
            # Validation
            if not job_id:
                return jsonify({"ok": False, "error": "missing_job_id", "message": "job_id is required"}), 400
            if not date:
                return jsonify({"ok": False, "error": "missing_date", "message": "date is required"}), 400
            if duration_minutes is None:
                return jsonify({"ok": False, "error": "missing_duration", "message": "duration_minutes is required"}), 400
            if duration_minutes <= 0:
                return jsonify({"ok": False, "error": "invalid_duration", "message": "duration_minutes must be greater than 0"}), 400
            
            # Validate job exists
            job = db.execute("SELECT id FROM jobs WHERE id = ?", (job_id,)).fetchone()
            if not job:
                return jsonify({"ok": False, "error": "job_not_found", "message": f"Job {job_id} does not exist"}), 400
            
            # Validate work_type
            valid_work_types = ["manual", "machine", "planning", "supervision", "transport", "training", "other"]
            if work_type not in valid_work_types:
                return jsonify({"ok": False, "error": "invalid_work_type", "message": f"work_type must be one of: {', '.join(valid_work_types)}"}), 400
            
            # Training ID - pouze pokud je work_type = "training"
            training_id = None
            if work_type == "training":
                training_id = data.get("training_id")
                if training_id:
                    # Validate training exists
                    training = db.execute("SELECT id FROM trainings WHERE id = ?", (training_id,)).fetchone()
                    if not training:
                        return jsonify({"ok": False, "error": "training_not_found", "message": f"Training {training_id} does not exist"}), 400
            
            # Get user_id from current user or employee_id
            user_id = u.get("id") if u else None
            employee_id = data.get("employee_id")
            if not employee_id and user_id:
                # Try to find employee_id from user_id
                emp = db.execute("SELECT id FROM employees WHERE user_id = ?", (user_id,)).fetchone()
                if emp:
                    employee_id = emp["id"]
            
            if not employee_id:
                return jsonify({"ok": False, "error": "missing_employee_id", "message": "employee_id is required"}), 400
            
            # Optional fields
            start_time = data.get("start_time")
            end_time = data.get("end_time")
            location = data.get("location")
            task_id = data.get("task_id")
            material_used = json.dumps(data.get("material_used")) if data.get("material_used") else None
            weather_snapshot = json.dumps(data.get("weather_snapshot")) if data.get("weather_snapshot") else None
            performance_signal = data.get("performance_signal", "normal")
            delay_reason = data.get("delay_reason")
            photo_url = data.get("photo_url")
            note = data.get("note")
            ai_flags = json.dumps(data.get("ai_flags")) if data.get("ai_flags") else None
            
            # Validate performance_signal
            valid_signals = ["fast", "normal", "slow", "blocked"]
            if performance_signal not in valid_signals:
                performance_signal = "normal"
            
            # Calculate hours for backwards compatibility
            hours = duration_minutes / 60.0
            
            # Calculate labor_cost using hourly rate hierarchy
            labor_cost = None
            try:
                hourly_rate = _get_hourly_rate(db, job_id=job_id, employee_id=employee_id, user_id=u.get("id"))
                labor_cost = (duration_minutes / 60.0) * float(hourly_rate)
            except Exception as e:
                print(f"[WORKLOG] Error calculating labor_cost: {e}")
                pass
            
            # Insert
            worklog_id = db.execute("""
                INSERT INTO timesheets(
                    user_id, employee_id, job_id, task_id, date,
                    duration_minutes, hours, work_type,
                    start_time, end_time, location, place,
                    note, activity, material_used, weather_snapshot,
                    performance_signal, delay_reason, photo_url, ai_flags,
                    labor_cost, training_id, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'))
            """, (
                user_id, employee_id, job_id, task_id, _normalize_date(date),
                duration_minutes, hours, work_type,
                start_time, end_time, location, location,
                note, note, material_used, weather_snapshot,
                performance_signal, delay_reason, photo_url, ai_flags,
                labor_cost, training_id
            )).lastrowid
            db.commit()
            
            # Pokud je to školení, automaticky přidej zaměstnance jako účastníka školení
            if training_id and employee_id:
                try:
                    # Zkontroluj, jestli už není účastníkem
                    existing_attendee = db.execute(
                        "SELECT id FROM training_attendees WHERE training_id = ? AND employee_id = ?",
                        (training_id, employee_id)
                    ).fetchone()
                    
                    if not existing_attendee:
                        # Přidej jako účastníka se statusem "registered"
                        db.execute("""
                            INSERT INTO training_attendees (training_id, employee_id, status, attendance_confirmed)
                            VALUES (?, ?, 'registered', 0)
                        """, (training_id, employee_id))
                        db.commit()
                        print(f"[WORKLOG] Automaticky přidán zaměstnanec {employee_id} jako účastník školení {training_id}")
                except Exception as e:
                    print(f"[WORKLOG] Error adding training attendee: {e}")
                    # Necháme pokračovat - není kritická chyba
            
            # Process material_used: deduct from warehouse
            if material_used:
                try:
                    materials = json.loads(material_used) if isinstance(material_used, str) else material_used
                    if isinstance(materials, list):
                        _process_material_usage(db, materials, job_id, "deduct")
                except Exception as e:
                    print(f"[WORKLOG] Error processing materials: {e}")
            
            # Recalculate job aggregations
            _recalculate_job_aggregations(db, job_id)
            
            # Check for worklog-related notifications
            _check_worklog_notifications(db, job_id, user_id=user_id, employee_id=employee_id)
            
            return jsonify({"ok": True, "message": "Work log created successfully"})
        except Exception as e:
            db.rollback()
            print(f"✗ Error creating work log: {e}")
            return jsonify({"ok": False, "error": "server_error", "message": str(e)}), 500
    
    if request.method == "PUT":
        # PUT: Update work log
        try:
            data = request.get_json(force=True, silent=True) or {}
            worklog_id = data.get("id")
            
            if not worklog_id:
                return jsonify({"ok": False, "error": "missing_id", "message": "id is required"}), 400
            
            # Check if work log exists
            existing = db.execute("SELECT job_id FROM timesheets WHERE id = ?", (worklog_id,)).fetchone()
            if not existing:
                return jsonify({"ok": False, "error": "not_found", "message": f"Work log {worklog_id} not found"}), 404
            
            old_job_id = existing["job_id"]
            
            # Build update query
            allowed_fields = {
                "job_id": int,
                "task_id": lambda x: int(x) if x else None,
                "date": _normalize_date,
                "duration_minutes": int,
                "work_type": str,
                "start_time": str,
                "end_time": str,
                "location": str,
                "task_id": lambda x: int(x) if x else None,
                "performance_signal": str,
                "delay_reason": str,
                "photo_url": str,
                "note": str,
                "training_id": lambda x: int(x) if x else None,
            }
            
            sets = []
            vals = []
            
            for field, converter in allowed_fields.items():
                if field in data:
                    value = converter(data[field])
                    if field == "duration_minutes" and value is not None:
                        if value <= 0:
                            return jsonify({"ok": False, "error": "invalid_duration", "message": "duration_minutes must be greater than 0"}), 400
                        # Update hours for backwards compatibility
                        sets.append("hours = ?")
                        vals.append(value / 60.0)
                    sets.append(f"{field} = ?")
                    vals.append(value)
            
            # Handle JSON fields
            if "material_used" in data:
                # Get old material_used to return it
                old_material = db.execute("SELECT material_used FROM timesheets WHERE id = ?", (worklog_id,)).fetchone()
                if old_material and old_material.get("material_used"):
                    try:
                        old_materials = json.loads(old_material["material_used"])
                        if isinstance(old_materials, list):
                            _process_material_usage(db, old_materials, old_job_id, "return")
                    except:
                        pass
                
                # Process new material_used
                new_material_used = json.dumps(data["material_used"]) if data["material_used"] else None
                sets.append("material_used = ?")
                vals.append(new_material_used)
                
                # Deduct new materials
                if data.get("material_used"):
                    try:
                        materials = data["material_used"] if isinstance(data["material_used"], list) else json.loads(data["material_used"])
                        new_job_id = data.get("job_id", old_job_id)
                        if isinstance(materials, list):
                            _process_material_usage(db, materials, new_job_id, "deduct")
                    except:
                        pass
            if "weather_snapshot" in data:
                sets.append("weather_snapshot = ?")
                vals.append(json.dumps(data["weather_snapshot"]) if data["weather_snapshot"] else None)
            if "ai_flags" in data:
                sets.append("ai_flags = ?")
                vals.append(json.dumps(data["ai_flags"]) if data["ai_flags"] else None)
            
            # Validate work_type if provided
            if "work_type" in data:
                valid_work_types = ["manual", "machine", "planning", "supervision", "transport", "training", "other"]
                if data["work_type"] not in valid_work_types:
                    return jsonify({"ok": False, "error": "invalid_work_type", "message": f"work_type must be one of: {', '.join(valid_work_types)}"}), 400
            
            # Training ID - pouze pokud je work_type = "training"
            if "training_id" in data or "work_type" in data:
                work_type = data.get("work_type")
                if work_type == "training":
                    training_id = data.get("training_id")
                    if training_id:
                        # Validate training exists
                        training = db.execute("SELECT id FROM trainings WHERE id = ?", (training_id,)).fetchone()
                        if not training:
                            return jsonify({"ok": False, "error": "training_not_found", "message": f"Training {training_id} does not exist"}), 400
                        sets.append("training_id = ?")
                        vals.append(training_id)
                    else:
                        sets.append("training_id = ?")
                        vals.append(None)
                elif work_type and work_type != "training":
                    # Pokud se změnil work_type na něco jiného než training, vymaž training_id
                    sets.append("training_id = ?")
                    vals.append(None)
            
            # Validate performance_signal if provided
            if "performance_signal" in data:
                valid_signals = ["fast", "normal", "slow", "blocked"]
                if data["performance_signal"] not in valid_signals:
                    return jsonify({"ok": False, "error": "invalid_performance_signal", "message": f"performance_signal must be one of: {', '.join(valid_signals)}"}), 400
            
            if not sets:
                return jsonify({"ok": False, "error": "no_fields", "message": "No fields to update"}), 400
            
            # Recalculate labor_cost if duration_minutes changed
            if "duration_minutes" in data:
                try:
                    # Get hourly_rate
                    emp_id_result = db.execute("SELECT employee_id FROM timesheets WHERE id = ?", (worklog_id,)).fetchone()
                    if emp_id_result:
                        emp_rate = db.execute("SELECT hourly_rate FROM employees WHERE id = ?", (emp_id_result["employee_id"],)).fetchone()
                        hourly_rate = emp_rate["hourly_rate"] if emp_rate and emp_rate.get("hourly_rate") else 200
                        labor_cost = (data["duration_minutes"] / 60.0) * float(hourly_rate)
                        sets.append("labor_cost = ?")
                        vals.append(labor_cost)
                except:
                    pass
            
            vals.append(worklog_id)
            db.execute(f"UPDATE timesheets SET {', '.join(sets)} WHERE id = ?", vals)
            db.commit()
            
            # Pokud se změnil training_id, aktualizuj účastníky školení
            if "training_id" in data or "work_type" in data:
                try:
                    # Získej aktuální data worklogu po update
                    updated_worklog = db.execute(
                        "SELECT training_id, employee_id, work_type FROM timesheets WHERE id = ?",
                        (worklog_id,)
                    ).fetchone()
                    
                    if updated_worklog:
                        new_training_id = updated_worklog.get("training_id")
                        employee_id = updated_worklog.get("employee_id")
                        work_type = updated_worklog.get("work_type")
                        
                        # Pokud je work_type = "training" a má training_id, přidej účastníka
                        if work_type == "training" and new_training_id and employee_id:
                            existing_attendee = db.execute(
                                "SELECT id FROM training_attendees WHERE training_id = ? AND employee_id = ?",
                                (new_training_id, employee_id)
                            ).fetchone()
                            
                            if not existing_attendee:
                                db.execute("""
                                    INSERT INTO training_attendees (training_id, employee_id, status, attendance_confirmed)
                                    VALUES (?, ?, 'registered', 0)
                                """, (new_training_id, employee_id))
                                db.commit()
                                print(f"[WORKLOG] Automaticky přidán zaměstnanec {employee_id} jako účastník školení {new_training_id}")
                except Exception as e:
                    print(f"[WORKLOG] Error updating training attendee: {e}")
                    # Necháme pokračovat
            
            # Recalculate job aggregations for old and new job
            new_job_id = data.get("job_id", old_job_id)
            _recalculate_job_aggregations(db, old_job_id)
            _check_worklog_notifications(db, old_job_id, user_id=user_id, employee_id=employee_id)
            if new_job_id != old_job_id:
                _recalculate_job_aggregations(db, new_job_id)
                _check_worklog_notifications(db, new_job_id, user_id=user_id, employee_id=employee_id)
            
            return jsonify({"ok": True, "message": "Work log updated successfully"})
        except Exception as e:
            db.rollback()
            print(f"✗ Error updating work log: {e}")
            return jsonify({"ok": False, "error": "server_error", "message": str(e)}), 500
    
    # DELETE
    if request.method == "DELETE":
        try:
            worklog_id = request.args.get("id", type=int)
            if not worklog_id:
                return jsonify({"ok": False, "error": "missing_id", "message": "id parameter is required"}), 400
            
            # Get job_id and material_used before deletion for recalculation
            job_result = db.execute("SELECT job_id, material_used FROM timesheets WHERE id = ?", (worklog_id,)).fetchone()
            if not job_result:
                return jsonify({"ok": False, "error": "not_found", "message": f"Work log {worklog_id} not found"}), 404
            
            job_id = job_result["job_id"]
            material_used = job_result.get("material_used")
            
            # Return materials to warehouse
            if material_used:
                try:
                    materials = json.loads(material_used) if isinstance(material_used, str) else material_used
                    if isinstance(materials, list):
                        _process_material_usage(db, materials, job_id, "return")
                except Exception as e:
                    print(f"[WORKLOG] Error returning materials: {e}")
            
            db.execute("DELETE FROM timesheets WHERE id = ?", (worklog_id,))
            db.commit()
            
            # Recalculate job aggregations
            _recalculate_job_aggregations(db, job_id)
            
            # Check for worklog-related notifications
            _check_worklog_notifications(db, job_id, user_id=user_id, employee_id=employee_id)
            
            return jsonify({"ok": True, "message": "Work log deleted successfully"})
        except Exception as e:
            db.rollback()
            print(f"✗ Error deleting work log: {e}")
            return jsonify({"ok": False, "error": "server_error", "message": str(e)}), 500

# Warehouse items API
@timesheets_bp.route("/gd/api/worklogs/summary", methods=["GET"])
def gd_api_worklogs_summary():
    """Get summary statistics for worklogs"""
    u, err = require_role(write=False)
    if err:
        return err
    db = get_db()
    
    try:
        user_id = request.args.get("user_id", type=int)
        d_from = _normalize_date(request.args.get("from"))
        d_to = _normalize_date(request.args.get("to"))
        
        # Build WHERE clause
        conds = []
        params = []
        
        if user_id:
            conds.append("(user_id = ? OR (user_id IS NULL AND employee_id IN (SELECT id FROM employees WHERE user_id = ?)))")
            params.extend([user_id, user_id])
        if d_from and d_to:
            conds.append("date(date) BETWEEN date(?) AND date(?)")
            params.extend([d_from, d_to])
        elif d_from:
            conds.append("date(date) >= date(?)")
            params.append(d_from)
        elif d_to:
            conds.append("date(date) <= date(?)")
            params.append(d_to)
        
        where_clause = " WHERE " + " AND ".join(conds) if conds else ""
        
        # Calculate total_minutes
        total_result = db.execute(f"""
            SELECT COALESCE(SUM(COALESCE(duration_minutes, CAST(hours * 60 AS INTEGER))), 0) as total_minutes
            FROM timesheets
            {where_clause}
        """, params).fetchone()
        total_minutes = total_result['total_minutes'] or 0
        
        # Calculate avg_per_day
        days_result = db.execute(f"""
            SELECT COUNT(DISTINCT date) as days
            FROM timesheets
            {where_clause}
        """, params).fetchone()
        days_count = days_result['days'] or 1
        avg_per_day = total_minutes / days_count if days_count > 0 else 0
        
        # Calculate overtime_minutes (assuming 8h/day = 480 minutes)
        overtime_result = db.execute(f"""
            SELECT 
                date,
                SUM(COALESCE(duration_minutes, CAST(hours * 60 AS INTEGER))) as day_minutes
            FROM timesheets
            {where_clause}
            GROUP BY date
            HAVING day_minutes > 480
        """, params).fetchall()
        overtime_minutes = sum(max(0, row['day_minutes'] - 480) for row in overtime_result)
        
        # Top jobs
        top_jobs_result = db.execute(f"""
            SELECT 
                job_id,
                SUM(COALESCE(duration_minutes, CAST(hours * 60 AS INTEGER))) as total_minutes
            FROM timesheets
            {where_clause}
            GROUP BY job_id
            ORDER BY total_minutes DESC
            LIMIT 5
        """, params).fetchall()
        top_jobs = [{"job_id": row['job_id'], "total_minutes": row['total_minutes']} for row in top_jobs_result]
        
        # Efficiency (based on performance_signal)
        efficiency_result = db.execute(f"""
            SELECT 
                performance_signal,
                COUNT(*) as count
            FROM timesheets
            {where_clause} AND performance_signal IS NOT NULL
            GROUP BY performance_signal
        """, params).fetchall()
        
        total_signals = sum(row['count'] for row in efficiency_result)
        fast_count = next((row['count'] for row in efficiency_result if row['performance_signal'] == 'fast'), 0)
        slow_count = next((row['count'] for row in efficiency_result if row['performance_signal'] == 'slow'), 0)
        blocked_count = next((row['count'] for row in efficiency_result if row['performance_signal'] == 'blocked'), 0)
        
        efficiency = (fast_count / total_signals * 100) if total_signals > 0 else 0
        
        # Anomalies count (overtime + blocked + delay)
        anomalies_result = db.execute(f"""
            SELECT COUNT(*) as count
            FROM (
                SELECT date, SUM(COALESCE(duration_minutes, CAST(hours * 60 AS INTEGER))) as day_minutes
                FROM timesheets
                {where_clause}
                GROUP BY date
                HAVING day_minutes > 480
            ) overtime_days
        """, params).fetchone()
        overtime_days = anomalies_result['count'] or 0
        
        blocked_anomalies = db.execute(f"""
            SELECT COUNT(*) as count
            FROM timesheets
            {where_clause} AND performance_signal = 'blocked'
        """, params).fetchone()
        blocked_count = blocked_anomalies['count'] or 0
        
        delay_anomalies = db.execute(f"""
            SELECT COUNT(*) as count
            FROM timesheets
            {where_clause} AND delay_reason IS NOT NULL AND delay_reason != ''
        """, params).fetchone()
        delay_count = delay_anomalies['count'] or 0
        
        anomalies_count = overtime_days + blocked_count + delay_count
        
        return jsonify({
            "ok": True,
            "summary": {
                "total_minutes": int(total_minutes),
                "avg_per_day": round(avg_per_day, 1),
                "overtime_minutes": int(overtime_minutes),
                "top_jobs": top_jobs,
                "efficiency": round(efficiency, 1),
                "anomalies_count": anomalies_count
            }
        })
    except Exception as e:
        print(f"✗ Error getting worklogs summary: {e}")
        return jsonify({"ok": False, "error": "server_error", "message": str(e)}), 500

@timesheets_bp.route("/gd/api/worklogs/heatmap", methods=["GET"])
def gd_api_worklogs_heatmap():
    """Get heatmap data for worklogs"""
    u, err = require_role(write=False)
    if err:
        return err
    db = get_db()
    
    try:
        user_id = request.args.get("user_id", type=int)
        d_from = _normalize_date(request.args.get("from"))
        d_to = _normalize_date(request.args.get("to"))
        
        # Default to last 30 days if no range specified
        if not d_from or not d_to:
            from datetime import datetime, timedelta
            today = datetime.now().date()
            d_to = today.strftime('%Y-%m-%d')
            d_from = (today - timedelta(days=30)).strftime('%Y-%m-%d')
        
        # Build WHERE clause with table prefixes
        conds = ["date(t.date) BETWEEN date(?) AND date(?)"]
        params = [d_from, d_to]
        
        if user_id:
            conds.append("(t.user_id = ? OR (t.user_id IS NULL AND t.employee_id IN (SELECT id FROM employees WHERE user_id = ?)))")
            params.extend([user_id, user_id])
        
        where_clause = " WHERE " + " AND ".join(conds)
        
        # Get daily aggregates
        daily_result = db.execute(f"""
            SELECT 
                t.date,
                SUM(COALESCE(t.duration_minutes, CAST(t.hours * 60 AS INTEGER))) as total_minutes,
                COUNT(*) as entries,
                SUM(CASE WHEN t.performance_signal = 'blocked' THEN 1 ELSE 0 END) as blocked_count,
                SUM(CASE WHEN t.delay_reason IS NOT NULL AND t.delay_reason != '' THEN 1 ELSE 0 END) as delay_count
            FROM timesheets t
            {where_clause}
            GROUP BY t.date
            ORDER BY t.date ASC
        """, params).fetchall()
        
        heatmap_data = []
        for row in daily_result:
            total_minutes = row['total_minutes'] or 0
            # Calculate load_level: 0: <4h, 1: 4-6h, 2: 6-8h, 3: >8h
            if total_minutes < 240:  # < 4h
                load_level = 0
            elif total_minutes < 360:  # 4-6h
                load_level = 1
            elif total_minutes <= 480:  # 6-8h
                load_level = 2
            else:  # > 8h
                load_level = 3
            
            # Build flags
            flags = []
            if total_minutes > 480:
                flags.append("overtime")
            if row['blocked_count'] > 0:
                flags.append("blocked")
            if row['delay_count'] > 0:
                flags.append("delay")
            
            heatmap_data.append({
                "date": row['date'],
                "total_minutes": int(total_minutes),
                "load_level": load_level,
                "flags": flags
            })
        
        # Get per-user daily aggregates (for timeline view)
        per_user_result = db.execute(f"""
            SELECT 
                t.date,
                COALESCE(t.user_id, (SELECT user_id FROM employees WHERE id = t.employee_id)) as user_id,
                e.name as user_name,
                SUM(COALESCE(t.duration_minutes, CAST(t.hours * 60 AS INTEGER))) as total_minutes,
                COUNT(*) as entries
            FROM timesheets t
            LEFT JOIN employees e ON e.id = t.employee_id
            {where_clause}
            GROUP BY t.date, user_id, e.name
            ORDER BY t.date ASC, user_id ASC
        """, params).fetchall()
        
        per_user_data = {}
        for row in per_user_result:
            date = row['date']
            user_id = row['user_id']
            if not date or not user_id:
                continue
            
            if date not in per_user_data:
                per_user_data[date] = []
            
            total_minutes = row['total_minutes'] or 0
            # Calculate load_level: 0: <4h, 1: 4-6h, 2: 6-8h, 3: >8h
            if total_minutes < 240:  # < 4h
                load_level = 0
            elif total_minutes < 360:  # 4-6h
                load_level = 1
            elif total_minutes <= 480:  # 6-8h
                load_level = 2
            else:  # > 8h
                load_level = 3
            
            per_user_data[date].append({
                "user_id": user_id,
                "user_name": row['user_name'] or f"User #{user_id}",
                "total_minutes": int(total_minutes),
                "load_level": load_level,
                "entries": row['entries'] or 0
            })
        
        return jsonify({
            "ok": True,
            "heatmap": heatmap_data,
            "per_user": per_user_data  # New: per-user data for timeline view
        })
    except Exception as e:
        print(f"✗ Error getting worklogs heatmap: {e}")
        return jsonify({"ok": False, "error": "server_error", "message": str(e)}), 500


@timesheets_bp.route("/gd/api/worklogs/ai-insights", methods=["GET"])
def gd_api_worklogs_ai_insights():
    """Get AI insights for worklogs - heuristics without LLM"""
    u, err = require_role(write=False)
    if err:
        return err
    db = get_db()
    
    try:
        from datetime import datetime, timedelta
        
        user_id = request.args.get("user_id", type=int)
        job_id = request.args.get("job_id", type=int)
        d_from = _normalize_date(request.args.get("from"))
        d_to = _normalize_date(request.args.get("to"))
        
        # Default to last 30 days if no range specified
        if not d_from or not d_to:
            today = datetime.now().date()
            d_to = today.strftime('%Y-%m-%d')
            d_from = (today - timedelta(days=30)).strftime('%Y-%m-%d')
        
        # Build WHERE clause
        conds = ["date(date) BETWEEN date(?) AND date(?)"]
        params = [d_from, d_to]
        
        if user_id:
            conds.append("(user_id = ? OR (user_id IS NULL AND employee_id IN (SELECT id FROM employees WHERE user_id = ?)))")
            params.extend([user_id, user_id])
        
        if job_id:
            conds.append("job_id = ?")
            params.append(job_id)
        
        where_clause = " WHERE " + " AND ".join(conds)
        
        # === 1. ANOMALY DAYS ===
        # anomaly_day: overtime + blocked signál + delay
        anomaly_days = []
        try:
            anomaly_rows = db.execute(f"""
                SELECT 
                    date,
                    SUM(COALESCE(duration_minutes, CAST(hours * 60 AS INTEGER))) as total_minutes,
                    SUM(CASE WHEN performance_signal = 'blocked' THEN 1 ELSE 0 END) as blocked_count,
                    SUM(CASE WHEN delay_reason IS NOT NULL AND delay_reason != '' THEN 1 ELSE 0 END) as delay_count
                FROM timesheets
                {where_clause}
                GROUP BY date
                HAVING total_minutes > 480 OR blocked_count > 0 OR delay_count > 0
                ORDER BY date DESC
            """, params).fetchall()
            
            for row in anomaly_rows:
                total_minutes = row['total_minutes'] or 0
                blocked_count = row['blocked_count'] or 0
                delay_count = row['delay_count'] or 0
                
                flags = []
                if total_minutes > 480:
                    flags.append('overtime')
                if blocked_count > 0:
                    flags.append('blocked')
                if delay_count > 0:
                    flags.append('delay')
                
                anomaly_days.append({
                    "date": row['date'],
                    "total_hours": round(total_minutes / 60, 1),
                    "flags": flags,
                    "severity": "high" if total_minutes > 600 or (blocked_count > 0 and delay_count > 0) else "medium"
                })
        except Exception as e:
            print(f"[AI-INSIGHTS] Error calculating anomaly_days: {e}")
        
        # === 2. SLOWDOWN JOBS ===
        # slowdown_job: rostoucí čas bez progressu
        slowdown_jobs = []
        try:
            if job_id:
                # For specific job, check if time is increasing without progress
                job_rows = db.execute(f"""
                    SELECT 
                        date,
                        SUM(COALESCE(duration_minutes, CAST(hours * 60 AS INTEGER))) as day_minutes
                    FROM timesheets
                    {where_clause}
                    GROUP BY date
                    ORDER BY date ASC
                """, params).fetchall()
                
                if len(job_rows) >= 3:
                    # Check if last 3 days show increasing time
                    last_3_days = [row['day_minutes'] or 0 for row in job_rows[-3:]]
                    if last_3_days[0] < last_3_days[1] < last_3_days[2]:
                        # Time is increasing - check if job progress is not increasing
                        job_info = db.execute("SELECT progress, completion_percent FROM jobs WHERE id = ?", (job_id,)).fetchone()
                        progress = job_info.get('progress') or job_info.get('completion_percent') or 0
                        
                        slowdown_jobs.append({
                            "job_id": job_id,
                            "trend": "increasing_time",
                            "last_3_days_hours": [round(m / 60, 1) for m in last_3_days],
                            "progress": progress,
                            "severity": "medium"
                        })
            else:
                # For all jobs, find jobs with increasing time
                job_trends = db.execute(f"""
                    SELECT 
                        job_id,
                        date,
                        SUM(COALESCE(duration_minutes, CAST(hours * 60 AS INTEGER))) as day_minutes
                    FROM timesheets
                    {where_clause}
                    GROUP BY job_id, date
                    ORDER BY job_id, date ASC
                """, params).fetchall()
                
                # Group by job_id
                jobs_by_id = {}
                for row in job_trends:
                    jid = row['job_id']
                    if jid not in jobs_by_id:
                        jobs_by_id[jid] = []
                    jobs_by_id[jid].append({
                        "date": row['date'],
                        "minutes": row['day_minutes'] or 0
                    })
                
                # Check each job for slowdown pattern
                for jid, days in jobs_by_id.items():
                    if len(days) >= 3:
                        last_3 = days[-3:]
                        minutes_3 = [d['minutes'] for d in last_3]
                        if minutes_3[0] < minutes_3[1] < minutes_3[2]:
                            # Time increasing - check progress
                            job_info = db.execute("SELECT progress, completion_percent FROM jobs WHERE id = ?", (jid,)).fetchone()
                            if job_info:
                                progress = job_info.get('progress') or job_info.get('completion_percent') or 0
                                slowdown_jobs.append({
                                    "job_id": jid,
                                    "trend": "increasing_time",
                                    "last_3_days_hours": [round(m / 60, 1) for m in minutes_3],
                                    "progress": progress,
                                    "severity": "medium"
                                })
        except Exception as e:
            print(f"[AI-INSIGHTS] Error calculating slowdown_jobs: {e}")
        
        # === 3. WORKLOAD RISK ===
        # workload_risk: 7denní průměr > threshold
        workload_risk = {
            "level": "low",
            "avg_hours_7d": 0,
            "threshold": 8,
            "users_at_risk": []
        }
        try:
            seven_days_ago = (datetime.now().date() - timedelta(days=7)).strftime('%Y-%m-%d')
            today_str = datetime.now().date().strftime('%Y-%m-%d')
            
            workload_conds = ["date(date) BETWEEN date(?) AND date(?)"]
            workload_params = [seven_days_ago, today_str]
            
            if user_id:
                workload_conds.append("(user_id = ? OR (user_id IS NULL AND employee_id IN (SELECT id FROM employees WHERE user_id = ?)))")
                workload_params.extend([user_id, user_id])
            
            workload_where = " WHERE " + " AND ".join(workload_conds)
            
            user_workloads = db.execute(f"""
                SELECT 
                    COALESCE(user_id, (SELECT user_id FROM employees WHERE id = employee_id)) as user_id,
                    e.name as user_name,
                    SUM(COALESCE(duration_minutes, CAST(hours * 60 AS INTEGER))) as total_minutes,
                    COUNT(DISTINCT date) as days_worked
                FROM timesheets t
                LEFT JOIN employees e ON e.id = t.employee_id
                {workload_where}
                GROUP BY user_id, e.name
            """, workload_params).fetchall()
            
            users_at_risk = []
            max_avg = 0
            
            for row in user_workloads:
                user_id_val = row['user_id']
                user_name = row['user_name'] or f"User #{user_id_val}"
                total_minutes = row['total_minutes'] or 0
                days_worked = row['days_worked'] or 1
                avg_hours = (total_minutes / 60) / days_worked
                
                if avg_hours > workload_risk['threshold']:
                    users_at_risk.append({
                        "user_id": user_id_val,
                        "user_name": user_name,
                        "avg_hours": round(avg_hours, 1),
                        "total_hours": round(total_minutes / 60, 1)
                    })
                
                max_avg = max(max_avg, avg_hours)
            
            workload_risk['avg_hours_7d'] = round(max_avg, 1)
            workload_risk['users_at_risk'] = users_at_risk
            
            if max_avg > 10:
                workload_risk['level'] = "critical"
            elif max_avg > 8:
                workload_risk['level'] = "high"
            elif max_avg > 6:
                workload_risk['level'] = "medium"
        except Exception as e:
            print(f"[AI-INSIGHTS] Error calculating workload_risk: {e}")
        
        # === 4. COST BURN RATE ===
        cost_burn_rate = {
            "daily_avg": 0,
            "weekly_total": 0,
            "trend": "stable"
        }
        try:
            cost_rows = db.execute(f"""
                SELECT 
                    date,
                    SUM(COALESCE(labor_cost, 0)) as daily_cost
                FROM timesheets
                {where_clause}
                GROUP BY date
                ORDER BY date DESC
                LIMIT 14
            """, params).fetchall()
            
            if cost_rows:
                daily_costs = [row['daily_cost'] or 0 for row in cost_rows]
                cost_burn_rate['daily_avg'] = round(sum(daily_costs) / len(daily_costs), 0)
                cost_burn_rate['weekly_total'] = round(sum(daily_costs[:7]), 0)
                
                if len(daily_costs) >= 7:
                    first_half = sum(daily_costs[7:]) / len(daily_costs[7:]) if len(daily_costs) > 7 else daily_costs[0]
                    second_half = sum(daily_costs[:7]) / 7
                    if second_half > first_half * 1.2:
                        cost_burn_rate['trend'] = "increasing"
                    elif second_half < first_half * 0.8:
                        cost_burn_rate['trend'] = "decreasing"
        except Exception as e:
            print(f"[AI-INSIGHTS] Error calculating cost_burn_rate: {e}")
        
        # === 5. PREDICTION HINT ===
        prediction_hint = None
        try:
            if anomaly_days:
                prediction_hint = f"Detekováno {len(anomaly_days)} anomálních dní s overtime nebo blokacemi"
            elif slowdown_jobs:
                prediction_hint = f"{len(slowdown_jobs)} zakázek vykazuje zpomalení"
            elif workload_risk['level'] != "low":
                prediction_hint = f"Vysoké zatížení týmu ({workload_risk['avg_hours_7d']}h/den průměr)"
            elif cost_burn_rate['trend'] == "increasing":
                prediction_hint = "Rostoucí náklady práce - zkontroluj efektivitu"
        except:
            pass
        
        return jsonify({
            "ok": True,
            "insights": {
                "workload_risk": workload_risk,
                "slowdown_jobs": slowdown_jobs,
                "anomaly_days": anomaly_days,
                "cost_burn_rate": cost_burn_rate,
                "prediction_hint": prediction_hint
            }
        })
    except Exception as e:
        print(f"✗ Error getting worklogs AI insights: {e}")
        return jsonify({"ok": False, "error": "server_error", "message": str(e)}), 500

# Helper function to recalculate job aggregations after worklog changes
