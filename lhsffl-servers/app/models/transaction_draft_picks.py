from app import db
from app.models.schemas.transaction_draft_picks import TransactionDraftPicksJSONSchema


class TransactionDraftPicks(db.Model):
    __tablename__ = 'TransactionDraftPicks'

    transaction_draft_pick_id = db.Column(db.Integer(), primary_key=True, autoincrement=True)

    transaction_id = db.Column(db.Integer(), db.ForeignKey('Transactions.transaction_id'), nullable=False)
    transaction = db.relationship('Transactions', back_populates='draft_pick_moves')

    season = db.Column(db.Integer(), nullable=False)

    round = db.Column(db.Integer(), nullable=False)

    roster_id = db.Column(db.Integer(), nullable=False)

    owner_id = db.Column(db.Integer(), nullable=True)

    previous_owner_id = db.Column(db.Integer(), nullable=True)

    def serialize(self):
        return TransactionDraftPicksJSONSchema().dump(self)
