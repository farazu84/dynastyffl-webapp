from marshmallow import Schema, fields


class TransactionWaiverBudgetJSONSchema(Schema):
    transaction_waiver_budget_id = fields.Int()
    transaction_id = fields.Int()
    sleeper_roster_id = fields.Int()
    amount = fields.Int()
