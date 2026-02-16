from marshmallow import Schema, fields


class TransactionPlayerTeamSchema(Schema):
    team_id = fields.Int()
    team_name = fields.Str()
    sleeper_roster_id = fields.Int()


class TransactionPlayerInfoSchema(Schema):
    player_id = fields.Int()
    first_name = fields.Str()
    last_name = fields.Str()
    position = fields.Str()
    position = fields.Str()
    nfl_team = fields.Str()
    sleeper_id = fields.Int()


class TransactionPlayersJSONSchema(Schema):
    transaction_player_id = fields.Int()
    transaction_id = fields.Int()
    player_sleeper_id = fields.Int()
    sleeper_roster_id = fields.Int()
    team = fields.Nested(TransactionPlayerTeamSchema)
    player = fields.Nested(TransactionPlayerInfoSchema)
    action = fields.Str()
