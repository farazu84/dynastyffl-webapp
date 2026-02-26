from .. import db
from app.models.schemas.bid_budget import BidBudgetJSONSchema


class BidBudget(db.Model):
    __tablename__ = 'BidBudget'
    __table_args__ = (
        db.UniqueConstraint('team_id', 'year', name='uq_bid_budget_team_year'),
    )

    bid_budget_id = db.Column(db.Integer(), primary_key=True, autoincrement=True)

    team_id = db.Column(db.Integer(), db.ForeignKey('Teams.team_id'), nullable=False)

    year = db.Column(db.Integer(), nullable=False)

    starting_balance = db.Column(db.Integer(), nullable=False, default=100)

    waiver_order = db.Column(db.Integer(), nullable=False)

    team = db.relationship('Teams', backref=db.backref('bid_budgets', lazy='select'))

    bids = db.relationship('UDFABids', back_populates='budget', lazy='select')

    @property
    def spent(self):
        """Total dollars spent on won bids."""
        return sum(b.amount for b in self.bids if b.status == 'won')

    @property
    def committed(self):
        """Total dollars tied up in pending bids."""
        return sum(b.amount for b in self.bids if b.status == 'pending')

    @property
    def available(self):
        """Dollars available to place new bids (balance minus pending commitments)."""
        return self.starting_balance - self.committed

    def serialize(self):
        return BidBudgetJSONSchema().dump(self)
