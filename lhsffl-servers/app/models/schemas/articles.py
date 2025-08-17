from marshmallow import Schema, fields
from app.models.schemas.article_teams import ArticleTeamsJSONSchema

class ArticlesJSONSchema(Schema):
    article_id = fields.Int()
    article_teams = fields.Nested(ArticleTeamsJSONSchema, many=True)
    article_type = fields.Str()
    author = fields.Str()
    title = fields.Str()
    content = fields.Str()
    thumbnail = fields.Str()
    creation_date = fields.DateTime()
