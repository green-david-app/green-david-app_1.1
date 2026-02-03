from marshmallow import Schema, fields, validate, validates_schema, ValidationError, post_load
from datetime import datetime


class TaskMaterialSchema(Schema):
    material_id = fields.Integer(allow_none=True)
    material_name = fields.String(required=True, validate=validate.Length(min=1, max=200))
    planned_quantity = fields.Float(required=True, validate=validate.Range(min=0))
    unit = fields.String(required=True, validate=validate.Length(min=1, max=20))


class TaskDependencyInputSchema(Schema):
    predecessor_task_id = fields.Integer(required=True)
    dependency_type = fields.String(required=True, validate=validate.OneOf([
        'finish_to_start', 'start_to_start', 'finish_to_finish',
        'material_produces', 'material_shares',
        'location_sequential', 'location_exclusive',
        'info_produces', 'info_validates'
    ]))
    lag_minutes = fields.Integer(load_default=0)
    is_hard = fields.Boolean(load_default=True)


class CreateTaskSchema(Schema):
    # === POVINNÁ POLE ===
    job_id = fields.Integer(required=True)
    title = fields.String(required=True, validate=validate.Length(min=3, max=200))
    task_type = fields.String(required=True, validate=validate.OneOf([
        'work', 'transport', 'admin', 'inspection', 'maintenance', 'delivery', 'meeting'
    ]))
    assigned_employee_id = fields.Integer(required=True)
    planned_start = fields.DateTime(required=True)
    planned_end = fields.DateTime(required=True)
    location_type = fields.String(required=True, validate=validate.OneOf([
        'job_site', 'warehouse', 'nursery', 'office', 'travel', 'client', 'supplier'
    ]))
    expected_outcome = fields.String(required=True, validate=validate.Length(min=10, max=1000))
    
    # === VOLITELNÁ POLE ===
    description = fields.String(validate=validate.Length(max=2000))
    expected_outcome_type = fields.String(validate=validate.OneOf([
        'installed', 'removed', 'transported', 'inspected', 'documented', 
        'planted', 'built', 'repaired', 'cleaned', 'measured'
    ]))
    expected_quantity = fields.Float()
    expected_unit = fields.String(validate=validate.Length(max=20))
    location_id = fields.Integer()
    location_name = fields.String(validate=validate.Length(max=200))
    gps_lat = fields.Float(validate=validate.Range(min=-90, max=90))
    gps_lng = fields.Float(validate=validate.Range(min=-180, max=180))
    priority = fields.String(load_default='normal', validate=validate.OneOf([
        'critical', 'high', 'normal', 'low'
    ]))
    
    # === VNOŘENÉ ===
    materials = fields.List(fields.Nested(TaskMaterialSchema), load_default=[])
    dependencies = fields.List(fields.Nested(TaskDependencyInputSchema), load_default=[])
    
    # === OFFLINE ===
    offline_uuid = fields.String(validate=validate.Length(max=36))
    created_offline = fields.Boolean(load_default=False)
    
    @validates_schema
    def validate_time_window(self, data, **kwargs):
        if data.get('planned_end') and data.get('planned_start'):
            if data['planned_end'] <= data['planned_start']:
                raise ValidationError('planned_end must be after planned_start')
            
            # Max 24 hodin pro jeden task
            duration = (data['planned_end'] - data['planned_start']).total_seconds() / 3600
            if duration > 24:
                raise ValidationError('Task duration cannot exceed 24 hours')


class UpdateTaskSchema(Schema):
    title = fields.String(validate=validate.Length(min=3, max=200))
    description = fields.String(validate=validate.Length(max=2000))
    assigned_employee_id = fields.Integer()
    planned_start = fields.DateTime()
    planned_end = fields.DateTime()
    expected_outcome = fields.String(validate=validate.Length(min=10, max=1000))
    priority = fields.String(validate=validate.OneOf(['critical', 'high', 'normal', 'low']))
    
    # Pro optimistic locking
    version = fields.Integer(required=True)
    
    @validates_schema
    def validate_time_window(self, data, **kwargs):
        if data.get('planned_end') and data.get('planned_start'):
            if data['planned_end'] <= data['planned_start']:
                raise ValidationError('planned_end must be after planned_start')


class StartTaskSchema(Schema):
    gps_lat = fields.Float(validate=validate.Range(min=-90, max=90))
    gps_lng = fields.Float(validate=validate.Range(min=-180, max=180))
    gps_accuracy = fields.Float()
    started_at = fields.DateTime()  # Optional, default = now
    offline = fields.Boolean(load_default=False)


class CompleteTaskSchema(Schema):
    completion_state = fields.String(required=True, validate=validate.OneOf([
        'done', 'partial', 'failed'
    ]))
    completion_percentage = fields.Integer(validate=validate.Range(min=0, max=100))
    completed_at = fields.DateTime()  # Optional, default = now
    deviation_notes = fields.String(validate=validate.Length(max=1000))
    
    # Materiály - skutečné množství
    materials_used = fields.List(fields.Dict(keys=fields.String(), values=fields.Raw()))
    
    # GPS
    gps_lat = fields.Float(validate=validate.Range(min=-90, max=90))
    gps_lng = fields.Float(validate=validate.Range(min=-180, max=180))
    
    offline = fields.Boolean(load_default=False)


class BlockTaskSchema(Schema):
    block_type = fields.String(required=True, validate=validate.OneOf([
        'material', 'weather', 'dependency', 'access', 'equipment', 'safety', 'other'
    ]))
    block_reason = fields.String(required=True, validate=validate.Length(min=5, max=500))
    blocking_entity_id = fields.Integer()  # material_id nebo task_id
    estimated_resolution = fields.DateTime()
    can_workaround = fields.Boolean(load_default=False)
    workaround_description = fields.String(validate=validate.Length(max=500))


class AddEvidenceSchema(Schema):
    evidence_type = fields.String(required=True, validate=validate.OneOf([
        'photo', 'note', 'measurement', 'gps_checkin', 'signature'
    ]))
    note_text = fields.String(validate=validate.Length(max=2000))
    measurement_value = fields.Float()
    measurement_unit = fields.String(validate=validate.Length(max=20))
    captured_at = fields.DateTime(required=True)
    gps_lat = fields.Float(validate=validate.Range(min=-90, max=90))
    gps_lng = fields.Float(validate=validate.Range(min=-180, max=180))
    gps_accuracy = fields.Float()
    captured_offline = fields.Boolean(load_default=False)


class SyncRequestSchema(Schema):
    device_id = fields.String(required=True, validate=validate.Length(max=100))
    last_sync_at = fields.DateTime(required=True)
    offline_changes = fields.List(fields.Dict(keys=fields.String(), values=fields.Raw()), load_default=[])
