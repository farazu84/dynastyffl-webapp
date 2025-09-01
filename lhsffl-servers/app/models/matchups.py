from app import db
from app.models.schemas.matchups import MatchupsJSONSchema

class Matchups(db.Model):
    __tablename__ = 'Matchups'
    
    matchup_id = db.Column(db.Integer(), primary_key=True, autoincrement=True)

    year = db.Column(db.Integer(), nullable=False)

    week = db.Column(db.Integer(), nullable=False)

    sleeper_matchup_id = db.Column(db.Integer(), nullable=False)

    sleeper_roster_id = db.Column(db.Integer(), db.ForeignKey('Teams.sleeper_roster_id'), nullable=False)

    team = db.relationship('Teams', 
                         foreign_keys=[sleeper_roster_id],
                         primaryjoin='Matchups.sleeper_roster_id == Teams.sleeper_roster_id')

    opponent_sleeper_roster_id = db.Column(db.Integer(), db.ForeignKey('Teams.sleeper_roster_id'), nullable=False)

    opponent_team = db.relationship('Teams', 
                              foreign_keys=[opponent_sleeper_roster_id],
                              primaryjoin='Matchups.opponent_sleeper_roster_id == Teams.sleeper_roster_id')

    points_for = db.Column(db.Float(), nullable=False, default=0)

    points_against = db.Column(db.Float(), nullable=False, default=0)

    completed = db.Column(db.Boolean(), nullable=False, default=False)

    def serialize(self):
        return MatchupsJSONSchema().dump(self)
