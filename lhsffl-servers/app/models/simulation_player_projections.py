from app import db
from sqlalchemy.orm import relationship


class SimulationPlayerProjections(db.Model):
    __tablename__ = 'SimulationPlayerProjections'

    projection_id = db.Column(db.Integer(), primary_key=True, autoincrement=True)

    simulation_id = db.Column(db.Integer(), db.ForeignKey('MatchupSimulations.simulation_id'), nullable=False)
    simulation = relationship('MatchupSimulations', back_populates='player_projections')

    player_id = db.Column(db.Integer(), db.ForeignKey('Players.player_id'), nullable=False)
    player = relationship('Players')

    # Which analyst persona made this prediction
    persona = db.Column(db.String(64), nullable=False)

    projected_score = db.Column(db.Float(), nullable=False)

    reasoning = db.Column(db.Text(), nullable=True)

    def serialize(self):
        return {
            'projection_id': self.projection_id,
            'simulation_id': self.simulation_id,
            'player_id': self.player_id,
            'persona': self.persona,
            'projected_score': self.projected_score,
            'reasoning': self.reasoning,
        }
