from enum import Enum
from typing import Tuple, List, Dict
from datetime import datetime
import json

# Lazy import get_db to avoid circular import
def get_db():
    from main import get_db as _get_db
    return _get_db()


class IntegrityMetric(Enum):
    DATA_COMPLETENESS = "data_completeness"
    TIME_ACCURACY = "time_accuracy"
    EVIDENCE_QUALITY = "evidence_quality"
    MATERIAL_CONSISTENCY = "material_consistency"
    PROCESS_COMPLIANCE = "process_compliance"
    LOCATION_VALIDITY = "location_validity"
    DEPENDENCY_INTEGRITY = "dependency_integrity"


class TaskIntegrityService:
    
    WEIGHTS = {
        IntegrityMetric.DATA_COMPLETENESS: 0.20,
        IntegrityMetric.TIME_ACCURACY: 0.20,
        IntegrityMetric.EVIDENCE_QUALITY: 0.15,
        IntegrityMetric.MATERIAL_CONSISTENCY: 0.15,
        IntegrityMetric.PROCESS_COMPLIANCE: 0.10,
        IntegrityMetric.LOCATION_VALIDITY: 0.10,
        IntegrityMetric.DEPENDENCY_INTEGRITY: 0.10,
    }
    
    THRESHOLDS = {
        'EXCELLENT': 90,
        'GOOD': 70,
        'WARNING': 50,
        'CRITICAL': 30,
        'FAILED': 10,
    }
    
    AI_TRUST_LEVELS = {
        'EXCELLENT': 1.0,
        'GOOD': 0.8,
        'WARNING': 0.5,
        'CRITICAL': 0.2,
        'FAILED': 0.0,
    }
    
    @staticmethod
    def calculate_data_completeness(task_dict: dict) -> Tuple[float, List[str]]:
        """100 = všechna povinná pole vyplněna, -10 za každé chybějící."""
        flags = []
        score = 100
        
        required_fields = [
            ('title', 'Chybí název'),
            ('job_id', 'Chybí vazba na zakázku'),
            ('assigned_employee_id', 'Chybí přiřazený pracovník'),
            ('planned_start', 'Chybí plánovaný začátek'),
            ('planned_end', 'Chybí plánovaný konec'),
            ('expected_outcome', 'Chybí očekávaný výstup'),
            ('location_type', 'Chybí typ lokace'),
        ]
        
        for field, flag_text in required_fields:
            if not task_dict.get(field):
                score -= 10
                flags.append(f"MISSING_REQUIRED:{flag_text}")
        
        recommended = [('description', -5), ('gps_lat', -5), ('location_name', -5)]
        for field, penalty in recommended:
            if not task_dict.get(field):
                score += penalty
                flags.append(f"MISSING_RECOMMENDED:{field}")
        
        return max(0, score), flags
    
    @staticmethod
    def calculate_time_accuracy(task_dict: dict) -> Tuple[float, List[str]]:
        """100 = actual = planned (±5%), -2 za každé 1% nad 5%."""
        flags = []
        
        status = task_dict.get('status', 'planned')
        
        if status in ['planned', 'assigned']:
            return 100, []
        
        if status == 'in_progress':
            planned_end_str = task_dict.get('planned_end')
            planned_duration = task_dict.get('planned_duration_minutes', 0)
            
            if planned_end_str:
                try:
                    if isinstance(planned_end_str, str):
                        planned_end = datetime.fromisoformat(planned_end_str.replace('Z', '+00:00'))
                    else:
                        planned_end = planned_end_str
                    
                    if datetime.utcnow() > planned_end:
                        overrun_minutes = (datetime.utcnow() - planned_end).total_seconds() / 60
                        overrun_pct = (overrun_minutes / planned_duration * 100) if planned_duration else 0
                        if overrun_pct > 50:
                            flags.append(f"SEVERE_OVERRUN:{overrun_pct:.0f}%")
                            return 30, flags
                        elif overrun_pct > 20:
                            return 60, [f"OVERRUN:{overrun_pct:.0f}%"]
                except:
                    pass
            return 100, []
        
        actual_duration = task_dict.get('actual_duration_minutes')
        planned_duration = task_dict.get('planned_duration_minutes')
        
        if not actual_duration or not planned_duration:
            return 50, ["MISSING_DURATION_DATA"]
        
        deviation_pct = abs(actual_duration - planned_duration) / planned_duration * 100
        
        if deviation_pct <= 5:
            return 100, []
        
        if deviation_pct > 50:
            flags.append(f"TIME_DEVIATION_SEVERE:{deviation_pct:.0f}%")
        elif deviation_pct > 20:
            flags.append(f"TIME_DEVIATION_HIGH:{deviation_pct:.0f}%")
        
        penalty = (deviation_pct - 5) * 2
        return max(0, 100 - penalty), flags
    
    @staticmethod
    def calculate_evidence_quality(task_dict: dict, evidences: List[dict] = None) -> Tuple[float, List[str]]:
        """100 = validované foto+poznámka, 0 = žádný důkaz u completed."""
        flags = []
        
        status = task_dict.get('status', 'planned')
        
        if status not in ['completed', 'partial', 'failed']:
            return 100, []
        
        if not evidences:
            return 0, ["NO_EVIDENCE"]
        
        score = 40
        has_photo = any(e.get('evidence_type') == 'photo' for e in evidences)
        has_note = any(e.get('evidence_type') == 'note' for e in evidences)
        has_validated = any(e.get('is_validated', False) for e in evidences)
        has_gps = any(e.get('gps_lat') is not None for e in evidences)
        
        if has_photo:
            score += 20
        else:
            flags.append("NO_PHOTO_EVIDENCE")
        if has_note:
            score += 15
        if has_validated:
            score += 15
        else:
            flags.append("EVIDENCE_NOT_VALIDATED")
        if has_gps:
            score += 10
        
        return min(100, score), flags
    
    @staticmethod
    def calculate_material_consistency(task_dict: dict, materials: List[dict] = None) -> Tuple[float, List[str]]:
        """100 = všechny materiály sedí (±10%), penalizace za odchylky."""
        flags = []
        
        if not materials:
            return 100, []
        
        score = 100
        
        for mat in materials:
            actual_qty = mat.get('actual_quantity')
            planned_qty = mat.get('planned_quantity', 0)
            
            if actual_qty is None or planned_qty == 0:
                continue
            
            deviation_pct = abs(actual_qty - planned_qty) / planned_qty * 100
            
            if deviation_pct > 10:
                score -= 5
                flags.append(f"MATERIAL_DEVIATION:{mat.get('material_name', 'unknown')}")
            
            if mat.get('substitute_used'):
                if not mat.get('substitute_notes'):
                    score -= 15
                    flags.append(f"SUBSTITUTE_WITHOUT_NOTES:{mat.get('material_name', 'unknown')}")
                else:
                    score -= 5
        
        return max(0, score), flags
    
    @staticmethod
    def calculate_process_compliance(task_dict: dict) -> Tuple[float, List[str]]:
        """Hodnotí dodržení procesních pravidel."""
        flags = []
        score = 100
        
        actual_start_str = task_dict.get('actual_start')
        actual_end_str = task_dict.get('actual_end')
        
        if actual_start_str and actual_end_str:
            try:
                if isinstance(actual_start_str, str):
                    actual_start = datetime.fromisoformat(actual_start_str.replace('Z', '+00:00'))
                else:
                    actual_start = actual_start_str
                
                if isinstance(actual_end_str, str):
                    actual_end = datetime.fromisoformat(actual_end_str.replace('Z', '+00:00'))
                else:
                    actual_end = actual_end_str
                
                if actual_start > actual_end:
                    flags.append("INVALID_TIME_SEQUENCE")
                    score -= 30
            except:
                pass
        
        if task_dict.get('has_workaround') and not task_dict.get('deviation_notes'):
            flags.append("WORKAROUND_WITHOUT_NOTES")
            score -= 20
        
        if task_dict.get('has_material_deviation') and not task_dict.get('deviation_notes'):
            flags.append("DEVIATION_WITHOUT_NOTES")
            score -= 15
        
        return max(0, score), flags
    
    @staticmethod
    def calculate_location_validity(task_dict: dict) -> Tuple[float, List[str]]:
        """Validuje GPS data."""
        status = task_dict.get('status', 'planned')
        
        if not task_dict.get('gps_lat') or not task_dict.get('gps_lng'):
            if status in ['completed', 'partial']:
                return 70, ["NO_GPS_ON_COMPLETION"]
            return 100, []
        return 100, []
    
    @staticmethod
    def calculate_dependency_integrity(task_dict: dict) -> Tuple[float, List[str]]:
        """Kontroluje konzistenci závislostí."""
        if task_dict.get('status') == 'blocked':
            return 80, ["TASK_BLOCKED"]
        return 100, []
    
    @staticmethod
    def calculate_full_integrity(task_dict: dict, evidences: List[dict] = None, materials: List[dict] = None) -> Tuple[float, List[str], Dict[str, float]]:
        """Vypočítá celkové TIS."""
        metrics = {}
        all_flags = []
        
        calculators = [
            (IntegrityMetric.DATA_COMPLETENESS, TaskIntegrityService.calculate_data_completeness),
            (IntegrityMetric.TIME_ACCURACY, TaskIntegrityService.calculate_time_accuracy),
            (IntegrityMetric.EVIDENCE_QUALITY, lambda t: TaskIntegrityService.calculate_evidence_quality(t, evidences)),
            (IntegrityMetric.MATERIAL_CONSISTENCY, lambda t: TaskIntegrityService.calculate_material_consistency(t, materials)),
            (IntegrityMetric.PROCESS_COMPLIANCE, TaskIntegrityService.calculate_process_compliance),
            (IntegrityMetric.LOCATION_VALIDITY, TaskIntegrityService.calculate_location_validity),
            (IntegrityMetric.DEPENDENCY_INTEGRITY, TaskIntegrityService.calculate_dependency_integrity),
        ]
        
        for metric, calculator in calculators:
            score, flags = calculator(task_dict)
            metrics[metric] = score
            all_flags.extend(flags)
        
        total_score = sum(metrics[m] * TaskIntegrityService.WEIGHTS[m] for m in metrics)
        breakdown = {m.value: metrics[m] for m in metrics}
        
        return round(total_score, 1), all_flags, breakdown
    
    @staticmethod
    def get_integrity_level(score: float) -> str:
        if score >= TaskIntegrityService.THRESHOLDS['EXCELLENT']:
            return 'EXCELLENT'
        elif score >= TaskIntegrityService.THRESHOLDS['GOOD']:
            return 'GOOD'
        elif score >= TaskIntegrityService.THRESHOLDS['WARNING']:
            return 'WARNING'
        elif score >= TaskIntegrityService.THRESHOLDS['CRITICAL']:
            return 'CRITICAL'
        return 'FAILED'
    
    @staticmethod
    def get_ai_trust_level(score: float) -> float:
        level = TaskIntegrityService.get_integrity_level(score)
        return TaskIntegrityService.AI_TRUST_LEVELS[level]
    
    @staticmethod
    def recalculate_and_update(task_id: int, emit_events: bool = True) -> dict:
        """Přepočítá integrity a uloží. Emituje event při významné změně."""
        db = get_db()
        
        # Get task
        task_row = db.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()
        if not task_row:
            raise ValueError(f"Task {task_id} not found")
        
        # Convert row to dict
        task_dict = dict(task_row)
        
        # Parse JSON fields
        integrity_flags_str = task_dict.get('integrity_flags', '[]')
        try:
            integrity_flags = json.loads(integrity_flags_str) if isinstance(integrity_flags_str, str) else integrity_flags_str
        except:
            integrity_flags = []
        
        old_score = task_dict.get('integrity_score', 100.0)
        old_level = TaskIntegrityService.get_integrity_level(old_score)
        
        # Get evidences and materials
        evidences_rows = db.execute("SELECT * FROM task_evidence WHERE task_id = ?", (task_id,)).fetchall()
        evidences = [dict(e) for e in evidences_rows]
        
        materials_rows = db.execute("SELECT * FROM task_materials WHERE task_id = ?", (task_id,)).fetchall()
        materials = [dict(m) for m in materials_rows]
        
        # Calculate new integrity
        new_score, flags, breakdown = TaskIntegrityService.calculate_full_integrity(
            task_dict, evidences=evidences, materials=materials
        )
        new_level = TaskIntegrityService.get_integrity_level(new_score)
        
        # Update task
        db.execute("""
            UPDATE tasks 
            SET integrity_score = ?, integrity_flags = ?
            WHERE id = ?
        """, (new_score, json.dumps(flags), task_id))
        db.commit()
        
        # Emit events if significant change
        if emit_events:
            try:
                import sys
                import os
                import importlib.util
                
                # Import TaskEventService directly
                _event_service_path = os.path.join(os.path.dirname(__file__), 'task_event_service.py')
                spec = importlib.util.spec_from_file_location("task_event_service", _event_service_path)
                event_service_module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(event_service_module)
                TaskEventService = event_service_module.TaskEventService
                
                # Import TaskEventType directly
                _event_types_path = os.path.join(os.path.dirname(__file__), '..', 'utils', 'event_types.py')
                spec = importlib.util.spec_from_file_location("event_types", _event_types_path)
                event_types_module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(event_types_module)
                TaskEventType = event_types_module.TaskEventType
                
                if old_score - new_score >= 10:
                    TaskEventService.emit(
                        task_id=task_id,
                        event_type=TaskEventType.TASK_INTEGRITY_DROPPED,
                        payload={
                            'previous_score': old_score,
                            'new_score': new_score,
                            'drop_amount': old_score - new_score,
                            'integrity_flags': flags,
                            'breakdown': breakdown,
                            'requires_attention': new_score < 50
                        },
                        source='system'
                    )
                
                if new_level == 'CRITICAL' and old_level != 'CRITICAL':
                    TaskEventService.emit(
                        task_id=task_id,
                        event_type=TaskEventType.TASK_INTEGRITY_CRITICAL,
                        payload={
                            'score': new_score,
                            'flags': flags,
                            'escalation_required': True
                        },
                        source='system'
                    )
            except Exception as e:
                # Don't fail if event emission fails
                print(f"[WARNING] Failed to emit integrity event: {e}")
        
        # Return updated task dict
        updated_task = db.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()
        return dict(updated_task)
