from app import db
from app.models.schemas.player_game_logs import PlayerGameLogsJSONSchema


class PlayerGameLogs(db.Model):
    __tablename__ = 'PlayerGameLogs'
    __table_args__ = (
        db.UniqueConstraint('gsis_id', 'season', 'week', name='uq_player_game_log'),
        db.Index('ix_player_game_logs_gsis', 'gsis_id'),
        db.Index('ix_player_game_logs_season_week', 'season', 'week'),
    )

    player_game_log_id = db.Column(db.Integer(), primary_key=True, autoincrement=True)

    gsis_id = db.Column(db.String(32), nullable=False)

    season = db.Column(db.Integer(), nullable=False)

    week = db.Column(db.Integer(), nullable=False)

    team = db.Column(db.String(8), nullable=True)

    targets = db.Column(db.Integer(), nullable=True)

    receptions = db.Column(db.Integer(), nullable=True)

    rec_air_yards = db.Column(db.Float(), nullable=True)

    rec_yards = db.Column(db.Float(), nullable=True)

    rec_touchdowns = db.Column(db.Integer(), nullable=True)

    rush_attempts = db.Column(db.Integer(), nullable=True)

    rush_yards = db.Column(db.Float(), nullable=True)

    rush_touchdowns = db.Column(db.Integer(), nullable=True)

    pass_touchdowns = db.Column(db.Integer(), nullable=True)

    fantasy_points_actual = db.Column(db.Float(), nullable=True)

    fantasy_points_expected = db.Column(db.Float(), nullable=True)

    fantasy_points_diff = db.Column(db.Float(), nullable=True)

    rec_first_downs = db.Column(db.Integer(), nullable=True)

    rush_first_downs = db.Column(db.Integer(), nullable=True)

    def serialize(self):
        return PlayerGameLogsJSONSchema().dump(self)
