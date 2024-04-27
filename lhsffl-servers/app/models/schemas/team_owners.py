from marshmallow import Schema, fields

class TeamOwnersJSONSchema(Schema):
    team_owner_id = fields.Int()
    user_id = fields.Int()
    sleeper_user_id = fields.Int()
    team_id = fields.Int()
    primary_owner = fields.Bool()