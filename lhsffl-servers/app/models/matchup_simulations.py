from app import db
from sqlalchemy.dialects.mysql import DATETIME, JSON
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship


class MatchupSimulations(db.Model):
    __tablename__ = 'MatchupSimulations'

    simulation_id = db.Column(db.Integer(), primary_key=True, autoincrement=True)

    matchup_id = db.Column(db.Integer(), db.ForeignKey('Matchups.matchup_id'), nullable=False)
    matchup = relationship('Matchups')

    week = db.Column(db.Integer(), nullable=False)

    year = db.Column(db.Integer(), nullable=False)

    team_a_win_probability = db.Column(db.Float(), nullable=False)

    team_a_median_score = db.Column(db.Float(), nullable=False)

    team_b_median_score = db.Column(db.Float(), nullable=False)

    # Interquartile range — high value means high disagreement / upset-prone
    team_a_score_spread = db.Column(db.Float(), nullable=False)

    team_b_score_spread = db.Column(db.Float(), nullable=False)

    # Raw audit trail: full array of all agent prediction objects
    agent_results = db.Column(JSON, nullable=False)

    n_agents = db.Column(db.Integer(), nullable=False)

    created_at = db.Column(DATETIME, nullable=False, default=func.now())

    player_projections = relationship('SimulationPlayerProjections', back_populates='simulation')

    def serialize(self):
        return {
            'simulation_id': self.simulation_id,
            'matchup_id': self.matchup_id,
            'week': self.week,
            'year': self.year,
            'team_a_win_probability': self.team_a_win_probability,
            'team_a_median_score': self.team_a_median_score,
            'team_b_median_score': self.team_b_median_score,
            'team_a_score_spread': self.team_a_score_spread,
            'team_b_score_spread': self.team_b_score_spread,
            'n_agents': self.n_agents,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }
