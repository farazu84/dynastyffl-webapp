from .. import db
from app.models.schemas.players import PlayersJSONSchema


class Players(db.Model):
    __tablename__ = 'Players'

    player_id = db.Column(db.Integer(), nullable=False, primary_key=True)

    first_name = db.Column(db.String(64), nullable=False)

    last_name = db.Column(db.String(64), nullable=False)

    birth_date = db.Column(db.String(64), default=False)

    team_id = db.Column(db.Integer(), db.ForeignKey('Teams.team_id'), nullable=True)
    team = db.relationship('Teams', back_populates='players')

    nfl_team = db.Column(db.String(64), nullable=True)

    college = db.Column(db.String(64), nullable=True)

    sleeper_id = db.Column(db.Integer(), nullable=False, default=False)

    years_exp = db.Column(db.Integer(), default=0)

    position = db.Column(db.Enum('QB', 'RB', 'WR', 'TE', 'K'), nullable=True)

    age = db.Column(db.Integer(), nullable=True)

    player_number = db.Column(db.Integer(), nullable=True)

    taxi = db.Column(db.Boolean(), default='0')

    starter = db.Column(db.Boolean(), default='0')

    height = db.Column(db.String(10), nullable=True)

    weight = db.Column(db.Integer(), nullable=True)

    high_school = db.Column(db.String(128), nullable=True)

    status = db.Column(db.String(64), nullable=True)

    active = db.Column(db.Boolean(), default='0')

    depth_chart_order = db.Column(db.Integer(), nullable=True)

    injury_status = db.Column(db.String(64), nullable=True)

    injury_body_part = db.Column(db.String(64), nullable=True)

    injury_start_date = db.Column(db.Date(), nullable=True)

    practice_participation = db.Column(db.String(32), nullable=True)

    espn_id = db.Column(db.Integer(), nullable=True)

    yahoo_id = db.Column(db.Integer(), nullable=True)

    fantasy_data_id = db.Column(db.Integer(), nullable=True)

    rotowire_id = db.Column(db.Integer(), nullable=True)

    rotoworld_id = db.Column(db.Integer(), nullable=True)

    sportradar_id = db.Column(db.String(64), nullable=True)

    stats_id = db.Column(db.Integer(), nullable=True)

    gsis_id = db.Column(db.String(32), nullable=True)

    oddsjam_id = db.Column(db.Integer(), nullable=True)

    pandascore_id = db.Column(db.Integer(), nullable=True)

    opta_id = db.Column(db.Integer(), nullable=True)

    swish_id = db.Column(db.Integer(), nullable=True)



    def serialize(self):
        return PlayersJSONSchema().dump(self)