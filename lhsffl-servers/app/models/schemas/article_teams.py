from marshmallow import Schema, fields

class ArticleTeamsJSONSchema(Schema):
    article_team_id = fields.Int()
    article_id = fields.Int()
    team_id = fields.Int()
    team = fields.Nested('TeamsJSONSchema', only=['team_id', 'team_name'])