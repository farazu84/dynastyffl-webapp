from marshmallow import Schema, fields


class BidBudgetJSONSchema(Schema):
    bid_budget_id = fields.Int()
    team_id = fields.Int()
    year = fields.Int()
    starting_balance = fields.Float()
    waiver_order = fields.Int()
    spent = fields.Float()
    committed = fields.Float()
    available = fields.Float()
    # The one fraction this team may spend, on a single bid. The frontend mirrors the fractional
    # bid rules against this, so it must be exposed rather than re-derived from starting_balance.
    cents = fields.Float()
