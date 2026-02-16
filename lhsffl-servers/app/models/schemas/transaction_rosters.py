from marshmallow import Schema, fields


class TransactionRosterTeamSchema(Schema):
    team_id = fields.Int()
    team_name = fields.Str()
    sleeper_roster_id = fields.Int()


class TransactionRostersJSONSchema(Schema):
    transaction_roster_id = fields.Int()
    transaction_id = fields.Int()
    sleeper_roster_id = fields.Int()
    team = fields.Nested(TransactionRosterTeamSchema)
    is_consenter = fields.Bool()
