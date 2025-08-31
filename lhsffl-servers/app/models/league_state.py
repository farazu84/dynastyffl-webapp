from app import db
from app.models.schemas.league_state import LeagueStateJSONSchema

class LeagueState(db.Model):
    __tablename__ = 'LeagueState'

    league_state_id = db.Column(db.Integer(), nullable=False, primary_key=True)

    year = db.Column(db.Integer(), nullable=False)

    week = db.Column(db.Integer(), nullable=False)

    current = db.Column(db.Boolean(), nullable=False, default=False)

    def serialize(self):
        return LeagueStateJSONSchema().dump(self)