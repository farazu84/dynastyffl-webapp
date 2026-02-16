from marshmallow import Schema, fields
from app.models.schemas.transaction_players import TransactionPlayersJSONSchema
from app.models.schemas.transaction_rosters import TransactionRostersJSONSchema
from app.models.schemas.transaction_draft_picks import TransactionDraftPicksJSONSchema
from app.models.schemas.transaction_waiver_budget import TransactionWaiverBudgetJSONSchema


class TransactionsJSONSchema(Schema):
    transaction_id = fields.Int()
    sleeper_transaction_id = fields.Int()
    year = fields.Int()
    week = fields.Int()
    type = fields.Str()
    status = fields.Str()
    creator_sleeper_user_id = fields.Int()
    sleeper_league_id = fields.Int()
    waiver_priority = fields.Int()
    created_at = fields.DateTime()
    status_updated_at = fields.DateTime()
    player_moves = fields.Nested(TransactionPlayersJSONSchema, many=True)
    roster_moves = fields.Nested(TransactionRostersJSONSchema, many=True)
    draft_pick_moves = fields.Nested(TransactionDraftPicksJSONSchema, many=True)
    waiver_budget_moves = fields.Nested(TransactionWaiverBudgetJSONSchema, many=True)


class TransactionsListJSONSchema(Schema):
    transaction_id = fields.Int()
    sleeper_transaction_id = fields.Int()
    year = fields.Int()
    week = fields.Int()
    type = fields.Str()
    status = fields.Str()
    created_at = fields.DateTime()
