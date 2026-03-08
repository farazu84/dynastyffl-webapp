from marshmallow import Schema, fields


class UDFABidsJSONSchema(Schema):
    bid_id = fields.Int()
    bid_budget_id = fields.Int()
    team_id = fields.Int()
    player_sleeper_id = fields.Int()
    year = fields.Int()
    amount = fields.Int()
    status = fields.Str()
    placed_at = fields.DateTime()
    updated_at = fields.DateTime()
