from .. import db


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

    year_exp = db.Column(db.Integer(), default=0)

    position = db.Column(db.Enum('QB', 'RB', 'WR', 'TE', 'K'), nullable=True)

    age = db.Column(db.Integer(), nullable=True)

    player_number = db.Column(db.Integer(), nullable=True)

    taxi = db.Column(db.Boolean(), default='0')

    starter = db.Column(db.Boolean(), default='0')