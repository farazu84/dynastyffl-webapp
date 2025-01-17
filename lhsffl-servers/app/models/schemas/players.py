from marshmallow import Schema, fields

class PlayersJSONSchema(Schema):
    #player_id = fields.Int()
    first_name = fields.Str()
    last_name = fields.Str()
    #birth_date = fields.Str()
    #team_id = fields.Int()
    nfl_team = fields.Str()
    #college = fields.Str()
    #sleeper_id = fields.Int()
    years_exp = fields.Int()
    position = fields.Str()
    age = fields.Int()
    #player_number = fields.Int()
    #taxi = fields.Bool()
    starter = fields.Bool()