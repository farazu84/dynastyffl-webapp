from marshmallow import Schema, fields


class BidBudgetJSONSchema(Schema):
    bid_budget_id = fields.Int()
    team_id = fields.Int()
    year = fields.Int()
    starting_balance = fields.Int()
    waiver_order = fields.Int()
    spent = fields.Int()
    committed = fields.Int()
    available = fields.Int()
