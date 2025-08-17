from .. import db

from sqlalchemy.orm import relationship

class ArticleTeams(db.Model):
    __tablename__ = 'ArticleTeams'

    article_team_id = db.Column(db.Integer(), nullable=False, primary_key=True)

    article_id = db.Column(db.Integer(), db.ForeignKey('Articles.article_id'), nullable=False)
    article = relationship('Articles', back_populates='article_teams')

    team_id = db.Column(db.Integer(), db.ForeignKey('Teams.team_id'), nullable=False)
    team = relationship('Teams', back_populates='article_teams')