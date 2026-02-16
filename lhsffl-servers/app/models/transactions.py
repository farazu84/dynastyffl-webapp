from app import db
from app.models.schemas.transactions import TransactionsJSONSchema


class Transactions(db.Model):
    __tablename__ = 'Transactions'

    transaction_id = db.Column(db.Integer(), primary_key=True, autoincrement=True)

    sleeper_transaction_id = db.Column(db.BigInteger(), nullable=False, unique=True)

    year = db.Column(db.Integer(), nullable=False)

    week = db.Column(db.Integer(), nullable=False)

    type = db.Column(db.Enum('trade', 'waiver', 'free_agent'), nullable=False)

    status = db.Column(db.String(32), nullable=False)

    creator_sleeper_user_id = db.Column(db.BigInteger(), nullable=True)

    sleeper_league_id = db.Column(db.BigInteger(), nullable=False)

    waiver_priority = db.Column(db.Integer(), nullable=True)

    created_at = db.Column(db.DateTime(), nullable=True)

    status_updated_at = db.Column(db.DateTime(), nullable=True)

    # Relationships
    player_moves = db.relationship('TransactionPlayers', back_populates='transaction', lazy='select')
    roster_moves = db.relationship('TransactionRosters', back_populates='transaction', lazy='select')
    draft_pick_moves = db.relationship('TransactionDraftPicks', back_populates='transaction', lazy='select')
    waiver_budget_moves = db.relationship('TransactionWaiverBudget', back_populates='transaction', lazy='select')

    def serialize(self):
        return TransactionsJSONSchema().dump(self)
