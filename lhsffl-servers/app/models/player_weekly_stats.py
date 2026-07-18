from app import db
from app.models.schemas.player_weekly_stats import PlayerWeeklyStatsJSONSchema


class PlayerWeeklyStats(db.Model):
    __tablename__ = 'PlayerWeeklyStats'
    __table_args__ = (
        db.UniqueConstraint('year', 'week', 'sleeper_roster_id', 'player_sleeper_id', name='uq_player_week'),
        db.Index('idx_player_weekly_player', 'player_sleeper_id'),
        db.Index('idx_player_weekly_roster_year_week', 'sleeper_roster_id', 'year', 'week'),
    )

    player_weekly_stat_id = db.Column(db.Integer(), primary_key=True, autoincrement=True)

    year = db.Column(db.Integer(), nullable=False)

    week = db.Column(db.Integer(), nullable=False)

    sleeper_roster_id = db.Column(db.Integer(), nullable=False)

    player_sleeper_id = db.Column(db.Integer(), nullable=False)

    points = db.Column(db.Float(), nullable=False, default=0)

    is_starter = db.Column(db.Boolean(), nullable=False, default=False)

    def serialize(self):
        return PlayerWeeklyStatsJSONSchema().dump(self)
