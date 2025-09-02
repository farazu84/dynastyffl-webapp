from marshmallow import fields, Schema
from app.models.schemas.teams import TeamsJSONSchema


class MatchupsJSONSchema(Schema):
    matchup_id = fields.Int()
    year = fields.Int()
    week = fields.Int()
    sleeper_matchup_id = fields.Int()
    sleeper_roster_id = fields.Int()
    team = fields.Nested(TeamsJSONSchema)
    opponent_sleeper_roster_id = fields.Int()
    opponent_team = fields.Nested(TeamsJSONSchema)
    points_for = fields.Float()
    points_against = fields.Float()
    completed = fields.Boolean()
