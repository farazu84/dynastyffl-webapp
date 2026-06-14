from app import db
from app.models.schemas.playoff_matchups import PlayoffMatchupsJSONSchema


class PlayoffMatchups(db.Model):
    __tablename__ = 'PlayoffMatchups'
    __table_args__ = (
        db.UniqueConstraint('year', 'bracket', 'sleeper_matchup_id', name='uq_playoff_matchup'),
        db.Index('idx_playoff_matchups_year_bracket', 'year', 'bracket'),
    )

    playoff_matchup_id = db.Column(db.Integer(), primary_key=True, autoincrement=True)

    year = db.Column(db.Integer(), nullable=False)

    round = db.Column(db.Integer(), nullable=False)

    bracket = db.Column(db.Enum('winners', 'losers'), nullable=False)

    sleeper_matchup_id = db.Column(db.Integer(), nullable=False)

    sleeper_roster_id = db.Column(db.Integer(), nullable=True)

    opponent_sleeper_roster_id = db.Column(db.Integer(), nullable=True)

    winner_sleeper_roster_id = db.Column(db.Integer(), nullable=True)

    loser_sleeper_roster_id = db.Column(db.Integer(), nullable=True)

    placement = db.Column(db.Integer(), nullable=True)

    def serialize(self):
        return PlayoffMatchupsJSONSchema().dump(self)
