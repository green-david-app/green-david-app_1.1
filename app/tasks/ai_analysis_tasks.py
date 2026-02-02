from datetime import datetime, timedelta
import json

# Lazy import get_db to avoid circular import
def get_db():
    from main import get_db as _get_db
    return _get_db()

# Import services
import sys
import os
import importlib.util

_ai_interface_path = os.path.join(os.path.dirname(__file__), '..', 'services', 'ai_operator_task_interface.py')
spec = importlib.util.spec_from_file_location("ai_operator_task_interface", _ai_interface_path)
ai_interface_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ai_interface_module)
AIOperatorTaskInterface = ai_interface_module.AIOperatorTaskInterface


def hourly_bottleneck_scan():
    """
    Každou hodinu skenuje bottlenecky a generuje alerty.
    """
    db = get_db()
    
    bottlenecks = AIOperatorTaskInterface.detect_bottlenecks({'all': True})
    
    alerts_created = 0
    
    for bn in bottlenecks:
        if bn['severity'] in ['critical', 'high']:
            # Check for duplicates - does alert already exist?
            entity_id = bn.get('entity_id')
            entity_type = bn.get('entity_type')
            
            # Check existing alerts
            existing_rows = db.execute("""
                SELECT id FROM ai_alerts 
                WHERE alert_type = 'bottleneck' 
                AND status = 'active'
                AND detail_data LIKE ?
            """, (f'%"entity_id":{entity_id}%',)).fetchall()
            
            if not existing_rows:
                detail_json = json.dumps(bn)
                recommended_json = json.dumps(bn.get('resolution_options', []))
                
                db.execute("""
                    INSERT INTO ai_alerts (
                        alert_type, severity, title, summary, detail_data,
                        job_id, task_id, employee_id, recommended_actions, created_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    'bottleneck',
                    bn['severity'],
                    bn['detail'],
                    bn['impact_assessment'],
                    detail_json,
                    bn.get('job_id'),
                    entity_id if entity_type == 'task' else None,
                    entity_id if entity_type == 'employee' else None,
                    recommended_json,
                    datetime.utcnow().isoformat()
                ))
                alerts_created += 1
    
    db.commit()
    
    return {
        'scanned_at': datetime.utcnow().isoformat(),
        'bottlenecks_found': len(bottlenecks),
        'alerts_created': alerts_created
    }


def daily_briefing_generation():
    """
    Každé ráno v 6:00 generuje denní briefing.
    """
    db = get_db()
    today = datetime.utcnow().date()
    
    # Check if already generated
    existing_row = db.execute("SELECT id FROM daily_briefings WHERE briefing_date = ?", (today.isoformat(),)).fetchone()
    if existing_row:
        return {'status': 'already_exists', 'briefing_id': existing_row[0]}
    
    # Generate briefing
    briefing_data = AIOperatorTaskInterface.generate_daily_briefing()
    
    full_data_json = json.dumps(briefing_data)
    
    db.execute("""
        INSERT INTO daily_briefings (
            briefing_date, generated_at, executive_summary, full_data,
            total_tasks, critical_items, integrity_average
        ) VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        today.isoformat(),
        datetime.utcnow().isoformat(),
        briefing_data['executive_summary'],
        full_data_json,
        briefing_data['todays_schedule']['total_tasks'],
        len([a for a in briefing_data['attention_items'] if a['priority'] == 'critical']),
        briefing_data['integrity_status'].get('average')
    ))
    
    db.commit()
    
    briefing_id = db.execute("SELECT last_insert_rowid()").fetchone()[0]
    
    # TODO: Send notification to management
    
    return {
        'status': 'generated',
        'briefing_id': briefing_id,
        'summary': briefing_data['executive_summary']
    }


def weekly_pattern_analysis():
    """
    Týdenní analýza vzorců pro dlouhodobé zlepšování.
    """
    db = get_db()
    
    patterns = AIOperatorTaskInterface.analyze_deviation_patterns(
        scope={},
        min_occurrences=5
    )
    
    significant_patterns = [p for p in patterns if p['confidence'] >= 0.7]
    
    alerts_created = 0
    for pattern in significant_patterns:
        # Create alert for significant patterns
        detail_json = json.dumps(pattern)
        recommended_json = json.dumps(pattern.get('recommended_actions', []))
        
        db.execute("""
            INSERT INTO ai_alerts (
                alert_type, severity, title, summary, detail_data,
                recommended_actions, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            'pattern',
            'warning',
            f"Recurring pattern: {pattern['reason']}",
            pattern['root_cause_hypothesis'],
            detail_json,
            recommended_json,
            datetime.utcnow().isoformat()
        ))
        alerts_created += 1
    
    db.commit()
    
    return {
        'analyzed_at': datetime.utcnow().isoformat(),
        'patterns_found': len(patterns),
        'significant_patterns': len(significant_patterns),
        'alerts_created': alerts_created
    }
