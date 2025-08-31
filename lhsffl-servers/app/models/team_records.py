from .. import db
from sqlalchemy.orm import relationship
from app.models.schemas.team_records import TeamRecordsJSONSchema


class TeamRecords(db.Model):
    __tablename__ = 'TeamRecords'

    team_record_id = db.Column(db.Integer(), nullable=False, primary_key=True)

    team_id = db.Column(db.Integer(), db.ForeignKey('Teams.team_id'), nullable=False)

    year = db.Column(db.Integer(), nullable=False)

    wins = db.Column(db.Integer(), nullable=False)

    losses = db.Column(db.Integer(), nullable=False)

    points_for = db.Column(db.Float(), nullable=False)

    points_against = db.Column(db.Float(), nullable=False)

    team = relationship('Teams', back_populates='team_records')

    def serialize(self):
        return TeamRecordsJSONSchema().dump(self)