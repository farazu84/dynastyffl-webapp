from marshmallow import Schema, fields


class TransactionDraftPicksJSONSchema(Schema):
    transaction_draft_pick_id = fields.Int()
    transaction_id = fields.Int()
    season = fields.Int()
    round = fields.Int()
    roster_id = fields.Int()
    owner_id = fields.Int()
    previous_owner_id = fields.Int()
