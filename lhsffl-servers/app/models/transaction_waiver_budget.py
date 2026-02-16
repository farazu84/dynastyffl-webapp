from app import db
from app.models.schemas.transaction_waiver_budget import TransactionWaiverBudgetJSONSchema


class TransactionWaiverBudget(db.Model):
    __tablename__ = 'TransactionWaiverBudget'

    transaction_waiver_budget_id = db.Column(db.Integer(), primary_key=True, autoincrement=True)

    transaction_id = db.Column(db.Integer(), db.ForeignKey('Transactions.transaction_id'), nullable=False)
    transaction = db.relationship('Transactions', back_populates='waiver_budget_moves')

    sleeper_roster_id = db.Column(db.Integer(), nullable=False)

    amount = db.Column(db.Integer(), nullable=False)

    def serialize(self):
        return TransactionWaiverBudgetJSONSchema().dump(self)
