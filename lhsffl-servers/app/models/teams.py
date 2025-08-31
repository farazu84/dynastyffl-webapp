from .. import db
from app.models.players import Players
from app.models.team_owners import TeamOwners
from app.models.schemas.teams import TeamsJSONSchema

from sqlalchemy.orm import relationship
from sqlalchemy.ext.associationproxy import association_proxy

class Teams(db.Model):
    __tablename__ = 'Teams'

    team_id = db.Column(db.Integer(), nullable=False, primary_key=True)

    team_name = db.Column(db.String(128), nullable=False, default='')

    championships = db.Column(db.Integer(), nullable=False, default=0)

    sleeper_roster_id = db.Column(db.Integer(), nullable=False)

    team_owners = relationship('TeamOwners', back_populates='team')

    owners = association_proxy('team_owners', 'user')

    article_teams = relationship('ArticleTeams', back_populates='team')

    players = relationship('Players', back_populates='team', order_by='Players.position')

    @property
    def starters(self):
        return [player for player in self.players if player.starter]

    @property
    def matchups(self):
        """Get matchups for this team by querying the database."""
        from app.models.matchups import Matchups
        return Matchups.query.filter_by(sleeper_roster_id=self.sleeper_roster_id).order_by(Matchups.week).all()

    def serialize(self):
        return TeamsJSONSchema().dump(self)


    @property
    def average_age(self):
        try:
            if not hasattr(self, 'players') or not self.players:
                return 0.0
            
            total_years = 0
            valid_players = 0
            
            for player in self.players:
                if hasattr(player, 'age') and player.age is not None and isinstance(player.age, (int, float)) and player.age > 0:
                    total_years += player.age
                    valid_players += 1
            
            if valid_players == 0:
                return 0.0
            
            return round(float(total_years) / float(valid_players), 2)
        except Exception as e:
            print(f"Error calculating average_age for team {getattr(self, 'team_name', 'Unknown')}: {e}")
            return 0.0

    @property
    def roster_size(self):
        try:
            if not hasattr(self, 'players') or not self.players:
                return 0
            return len(self.players)
        except Exception as e:
            print(f"Error calculating roster_size for team {getattr(self, 'team_name', 'Unknown')}: {e}")
            return 0

    @property
    def average_starter_age(self):
        try:
            if not hasattr(self, 'players') or not self.players:
                return 0.0
            
            total_years = 0
            starters = 0
            
            for player in self.players:
                if (hasattr(player, 'starter') and player.starter and 
                    hasattr(player, 'age') and player.age is not None and 
                    isinstance(player.age, (int, float)) and player.age > 0):
                    total_years += player.age
                    starters += 1
            
            if starters == 0:
                return 0.0
            
            return round(float(total_years) / float(starters), 2)
        except Exception as e:
            print(f"Error calculating average_starter_age for team {getattr(self, 'team_name', 'Unknown')}: {e}")
            return 0.0

    @property
    def articles(self):
        from app.models.articles import Articles

        return db.session.query(Articles).filter(Articles.article_teams.any(team_id=self.team_id), Articles.published == True).order_by(Articles.creation_date.desc()).all()
