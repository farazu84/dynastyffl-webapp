from marshmallow import Schema, fields


class TeamRecordsJSONSchema(Schema):
    team_record_id = fields.Int()
    team_id = fields.Int()
    year = fields.Int()
    wins = fields.Int()
    losses = fields.Int()
    points_for = fields.Float()
    points_against = fields.Float()