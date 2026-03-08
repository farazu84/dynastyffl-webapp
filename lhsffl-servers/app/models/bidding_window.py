from .. import db
from app.models.schemas.bidding_window import BiddingWindowJSONSchema
from datetime import datetime


class BiddingWindow(db.Model):
    __tablename__ = 'BiddingWindow'

    bidding_window_id = db.Column(db.Integer(), primary_key=True, autoincrement=True)

    year = db.Column(db.Integer(), nullable=False, unique=True)

    opens_at = db.Column(db.DateTime(), nullable=False)

    closes_at = db.Column(db.DateTime(), nullable=False)

    processed = db.Column(db.Boolean(), nullable=False, default=False)

    @property
    def is_open(self):
        now = datetime.utcnow()
        return self.opens_at <= now <= self.closes_at and not self.processed

    def serialize(self):
        return BiddingWindowJSONSchema().dump(self)
