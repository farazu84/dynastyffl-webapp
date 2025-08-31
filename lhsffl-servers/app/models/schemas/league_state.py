from marshmallow import Schema, fields

class LeagueStateJSONSchema(Schema):
    league_state_id = fields.Int()
    year = fields.Int()
    week = fields.Int()
    current = fields.Bool()