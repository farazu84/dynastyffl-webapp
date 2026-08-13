from decimal import Decimal

from .. import db
from app.logic.money import ZERO, cents_of, to_money
from app.models.schemas.bid_budget import BidBudgetJSONSchema


class BidBudget(db.Model):
    __tablename__ = 'BidBudget'
    __table_args__ = (
        db.UniqueConstraint('team_id', 'year', name='uq_bid_budget_team_year'),
    )

    bid_budget_id = db.Column(db.Integer(), primary_key=True, autoincrement=True)

    team_id = db.Column(db.Integer(), db.ForeignKey('Teams.team_id'), nullable=False)

    year = db.Column(db.Integer(), nullable=False)

    starting_balance = db.Column(db.Numeric(7, 2), nullable=False, default=Decimal('100.00'))

    waiver_order = db.Column(db.Integer(), nullable=False)

    team = db.relationship('Teams', backref=db.backref('bid_budgets', lazy='select'))

    bids = db.relationship('UDFABids', back_populates='budget', lazy='select')

    @property
    def spent(self):
        """Total dollars spent on won bids."""
        return sum((to_money(b.amount) for b in self.bids if b.status == 'won'), ZERO)

    @property
    def committed(self):
        """Total dollars tied up in pending bids."""
        return sum((to_money(b.amount) for b in self.bids if b.status == 'pending'), ZERO)

    @property
    def available(self):
        """Dollars available to place new bids (balance minus pending commitments)."""
        return to_money(self.starting_balance) - self.committed

    @property
    def cents(self):
        """
        The fractional part of the budget — the one fraction this team may spend, and only on a
        single bid. Decimal('0.00') for a whole-dollar budget, which means no fractional bid is
        legal at all. See validate_fractional_bid() for the rules this feeds.
        """
        return cents_of(self.starting_balance)

    def serialize(self):
        return BidBudgetJSONSchema().dump(self)
