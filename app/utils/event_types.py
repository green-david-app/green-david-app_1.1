from enum import Enum


class TaskEventType(Enum):
    # LIFECYCLE
    TASK_CREATED = "task_created"
    TASK_ASSIGNED = "task_assigned"
    TASK_REASSIGNED = "task_reassigned"
    TASK_SCHEDULED = "task_scheduled"
    TASK_RESCHEDULED = "task_rescheduled"
    
    # EXECUTION
    TASK_STARTED = "task_started"
    TASK_PAUSED = "task_paused"
    TASK_RESUMED = "task_resumed"
    TASK_COMPLETED = "task_completed"
    TASK_COMPLETED_PARTIAL = "task_completed_partial"
    TASK_FAILED = "task_failed"
    TASK_CANCELLED = "task_cancelled"
    
    # BLOKACE
    TASK_BLOCKED = "task_blocked"
    TASK_BLOCKED_MATERIAL = "task_blocked_material"
    TASK_BLOCKED_WEATHER = "task_blocked_weather"
    TASK_BLOCKED_DEPENDENCY = "task_blocked_dependency"
    TASK_BLOCKED_ACCESS = "task_blocked_access"
    TASK_UNBLOCKED = "task_unblocked"
    
    # ODCHYLKY
    TASK_DELAYED = "task_delayed"
    TASK_DEVIATION_TIME = "task_deviation_time"
    TASK_DEVIATION_MATERIAL = "task_deviation_material"
    TASK_WORKAROUND_USED = "task_workaround_used"
    
    # EVIDENCE
    TASK_EVIDENCE_ADDED = "task_evidence_added"
    TASK_EVIDENCE_VALIDATED = "task_evidence_validated"
    TASK_CHECKIN = "task_checkin"
    TASK_CHECKOUT = "task_checkout"
    
    # INTEGRITA
    TASK_INTEGRITY_DROPPED = "task_integrity_dropped"
    TASK_INTEGRITY_CRITICAL = "task_integrity_critical"
    TASK_INTEGRITY_RESTORED = "task_integrity_restored"
    
    # ZÁVISLOSTI
    TASK_DEPENDENCY_ADDED = "task_dependency_added"
    TASK_DEPENDENCY_RESOLVED = "task_dependency_resolved"
    TASK_DEPENDENCY_FAILED = "task_dependency_failed"
    TASK_RISK_PROPAGATED = "task_risk_propagated"
