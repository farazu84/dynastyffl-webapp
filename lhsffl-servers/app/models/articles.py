from .. import db
from sqlalchemy.dialects.mysql import DATETIME
from sqlalchemy.sql import func
from app.models.schemas.articles import ArticlesJSONSchema


class Articles(db.Model):
    __tablename__ = 'Articles'

    article_id = db.Column(db.Integer(), nullable=False, primary_key=True)

    article_type = db.Column(db.Enum('power_ranking', 'team_analysis', 'rumors', 'trade_analysis', 'injury', 'matchup_analysis', 'matchup_breakdown'), nullable=True)

    author = db.Column(db.String(64), nullable=True)

    title = db.Column(db.TEXT, nullable=False)

    content = db.Column(db.TEXT, nullable=False)

    thumbnail = db.Column(db.String(64), nullable=False)

    team_id = db.Column(db.Integer(), nullable=True)

    creation_date = db.Column(DATETIME, nullable=False, default=func.now())

    def serialize(self):
        return ArticlesJSONSchema().dump(self)