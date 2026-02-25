from marshmallow import Schema, fields

class UsersJSONSchema(Schema):
    user_id = fields.Int()
    user_name = fields.Str()
    first_name = fields.Str()
    last_name = fields.Str()
    sleeper_user_id = fields.Int()
    email = fields.Str()
    admin = fields.Bool()
    team_owner = fields.Bool()
