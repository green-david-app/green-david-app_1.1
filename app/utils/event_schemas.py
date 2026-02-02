"""
Payload schemas for TaskEvent types.
These define the expected structure of payload data for each event type.
"""

PAYLOAD_SCHEMAS = {
    "task_started": {
        "actual_start": "datetime",
        "gps_lat": "float|null",
        "gps_lng": "float|null",
        "planned_start": "datetime",
        "delay_minutes": "int"
    },
    "task_completed": {
        "actual_end": "datetime",
        "actual_duration_minutes": "int",
        "planned_duration_minutes": "int",
        "completion_state": "string",
        "completion_percentage": "int",
        "time_deviation_minutes": "int",
        "evidence_count": "int",
        "materials_summary": "object"
    },
    "task_completed_partial": {
        "actual_end": "datetime",
        "completion_percentage": "int",
        "remaining_work": "string",
        "reason": "string"
    },
    "task_blocked": {
        "block_reason": "string",
        "block_type": "string",
        "blocking_entity_id": "int|null",
        "estimated_resolution": "datetime|null",
        "can_workaround": "bool"
    },
    "task_blocked_material": {
        "missing_material_id": "int",
        "missing_material_name": "string",
        "required_quantity": "float",
        "available_quantity": "float",
        "estimated_arrival": "datetime|null"
    },
    "task_blocked_weather": {
        "weather_condition": "string",
        "forecast_hours": "int",
        "can_proceed_after": "datetime|null"
    },
    "task_blocked_dependency": {
        "dependency_task_id": "int",
        "dependency_status": "string",
        "dependency_completion_percentage": "int"
    },
    "task_blocked_access": {
        "location": "string",
        "access_issue": "string",
        "contact_person": "string|null"
    },
    "task_unblocked": {
        "was_blocked_by": "string",
        "resolution_method": "string",
        "block_duration_minutes": "int"
    },
    "task_delayed": {
        "planned_start": "datetime",
        "actual_start": "datetime|null",
        "delay_minutes": "int",
        "reason": "string"
    },
    "task_deviation_time": {
        "planned_duration_minutes": "int",
        "actual_duration_minutes": "int",
        "deviation_minutes": "int",
        "deviation_percentage": "float"
    },
    "task_deviation_material": {
        "material_id": "int",
        "planned_quantity": "float",
        "actual_quantity": "float",
        "deviation": "float",
        "substitute_used": "bool"
    },
    "task_workaround_used": {
        "original_plan": "string",
        "workaround_method": "string",
        "effectiveness": "string",
        "notes": "string"
    },
    "task_evidence_added": {
        "evidence_id": "int",
        "evidence_type": "string",
        "file_path": "string|null",
        "note_text": "string|null"
    },
    "task_evidence_validated": {
        "evidence_id": "int",
        "validated_by_id": "int",
        "validation_notes": "string|null"
    },
    "task_checkin": {
        "gps_lat": "float",
        "gps_lng": "float",
        "location_name": "string",
        "checkin_time": "datetime"
    },
    "task_checkout": {
        "gps_lat": "float",
        "gps_lng": "float",
        "location_name": "string",
        "checkout_time": "datetime",
        "work_duration_minutes": "int"
    },
    "task_integrity_dropped": {
        "previous_score": "float",
        "new_score": "float",
        "drop_amount": "float",
        "triggered_by": "string",
        "integrity_flags": "array",
        "requires_attention": "bool"
    },
    "task_integrity_critical": {
        "current_score": "float",
        "critical_threshold": "float",
        "integrity_flags": "array",
        "immediate_actions": "array"
    },
    "task_integrity_restored": {
        "previous_score": "float",
        "restored_score": "float",
        "restoration_method": "string",
        "integrity_flags_resolved": "array"
    },
    "task_dependency_added": {
        "dependency_task_id": "int",
        "dependency_type": "string",
        "is_blocking": "bool"
    },
    "task_dependency_resolved": {
        "dependency_task_id": "int",
        "dependency_completion_state": "string"
    },
    "task_dependency_failed": {
        "dependency_task_id": "int",
        "failure_reason": "string",
        "impact_on_current_task": "string"
    },
    "task_risk_propagated": {
        "source_task_id": "int",
        "risk_type": "string",
        "propagation_path": "array",
        "affected_tasks_count": "int",
        "estimated_impact_hours": "float"
    },
    "task_assigned": {
        "assigned_to_id": "int",
        "assigned_by_id": "int",
        "assignment_reason": "string|null"
    },
    "task_reassigned": {
        "previous_employee_id": "int",
        "new_employee_id": "int",
        "reassignment_reason": "string"
    },
    "task_scheduled": {
        "planned_start": "datetime",
        "planned_end": "datetime",
        "planned_duration_minutes": "int"
    },
    "task_rescheduled": {
        "previous_start": "datetime",
        "previous_end": "datetime",
        "new_start": "datetime",
        "new_end": "datetime",
        "reschedule_reason": "string"
    },
    "task_failed": {
        "failure_reason": "string",
        "failure_type": "string",
        "can_retry": "bool",
        "retry_after": "datetime|null"
    },
    "task_cancelled": {
        "cancellation_reason": "string",
        "cancelled_by_id": "int",
        "refund_required": "bool"
    }
}
