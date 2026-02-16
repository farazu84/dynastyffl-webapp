from app import db
from app.models.schemas.draft_picks import DraftPicksJSONSchema


class DraftPicks(db.Model):
    __tablename__ = 'DraftPicks'

    draft_pick_id = db.Column(db.Integer(), primary_key=True, autoincrement=True)

    season = db.Column(db.Integer(), nullable=False)

    round = db.Column(db.Integer(), nullable=False)

    pick_no = db.Column(db.Integer(), nullable=False)

    draft_slot = db.Column(db.Integer(), nullable=False)

    roster_id = db.Column(db.Integer(), nullable=False)

    player_sleeper_id = db.Column(db.Integer(), nullable=False)

    sleeper_draft_id = db.Column(db.BigInteger(), nullable=False)

    type = db.Column(db.Enum('startup', 'rookie', 'expansion'), nullable=False)

    def serialize(self):
        return DraftPicksJSONSchema().dump(self)
