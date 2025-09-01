from marshmallow import Schema, fields


class SyncStatusJSONSchema(Schema):
    sync_status_id = fields.Integer()
    sync_item = fields.String()
    timestamp = fields.DateTime()
    success = fields.Boolean()
    error = fields.String()