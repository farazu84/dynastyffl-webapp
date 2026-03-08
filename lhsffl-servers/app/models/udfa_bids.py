from .. import db
from app.models.schemas.udfa_bids import UDFABidsJSONSchema
from datetime import datetime


class UDFABids(db.Model):
    __tablename__ = 'UDFABids'
    __table_args__ = (
        db.UniqueConstraint('team_id', 'player_sleeper_id', 'year', name='uq_udfa_bid_team_player_year'),
    )

    bid_id = db.Column(db.Integer(), primary_key=True, autoincrement=True)

    bid_budget_id = db.Column(db.Integer(), db.ForeignKey('BidBudget.bid_budget_id'), nullable=False)

    team_id = db.Column(db.Integer(), db.ForeignKey('Teams.team_id'), nullable=False)

    player_sleeper_id = db.Column(db.Integer(), nullable=False)

    year = db.Column(db.Integer(), nullable=False)

    amount = db.Column(db.Integer(), nullable=False)

    status = db.Column(db.Enum('pending', 'won', 'lost'), nullable=False, default='pending')

    placed_at = db.Column(db.DateTime(), nullable=False, default=datetime.utcnow)

    updated_at = db.Column(db.DateTime(), nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    budget = db.relationship('BidBudget', back_populates='bids')

    team = db.relationship('Teams', backref=db.backref('udfa_bids', lazy='select'))

    @property
    def player(self):
        from app.models.players import Players
        return Players.query.filter_by(sleeper_id=self.player_sleeper_id).first()

    def serialize(self):
        return UDFABidsJSONSchema().dump(self)
