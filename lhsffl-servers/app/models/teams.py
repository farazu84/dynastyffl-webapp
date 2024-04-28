from .. import db
from app.models.players import Players
from app.models.team_owners import TeamOwners
from app.models.schemas.teams import TeamsJSONSchema

from sqlalchemy.orm import relationship

class Teams(db.Model):
    __tablename__ = 'Teams'

    team_id = db.Column(db.Integer(), nullable=False, primary_key=True)

    team_name = db.Column(db.String(128), nullable=False, default='')

    championships = db.Column(db.Integer(), nullable=False, default=0)

    team_owners = relationship('TeamOwners', back_populates='team')

    players = relationship('Players', back_populates='team', order_by='Players.position')



    def serialize(self):
        return TeamsJSONSchema().dump(self)



'''
    def get_all_teams():
        
        db.session.query.all()
'''
    