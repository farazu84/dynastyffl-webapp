from marshmallow import Schema, fields

class ArticlesJSONSchema(Schema):
    article_id = fields.Int()
    article_type = fields.Str()
    author = fields.Str()
    title = fields.Str()
    content = fields.Str()
    thumbnail = fields.Str()
    team_id = fields.Int()
    creation_date = fields.DateTime()
