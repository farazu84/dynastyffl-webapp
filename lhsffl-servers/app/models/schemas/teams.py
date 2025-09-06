from marshmallow import Schema, fields
from app.models.schemas.team_owners import TeamOwnersJSONSchema
from app.models.schemas.players import PlayersJSONSchema
from app.models.schemas.users import UsersJSONSchema
from app.models.schemas.articles import ArticlesJSONSchema
from app.models.schemas.team_records import TeamRecordsJSONSchema
#from app.models.schemas.matchups import MatchupsJSONSchema


class TeamsJSONSchema(Schema):
    team_id = fields.Int()
    team_name = fields.Str()
    championships = fields.Int()
    sleeper_roster_id = fields.Int()
    team_owners = fields.Nested(TeamOwnersJSONSchema, many=True)
    players = fields.Nested(PlayersJSONSchema, many=True)
    roster_size = fields.Int()
    average_age = fields.Float()
    average_starter_age = fields.Float()
    owners = fields.Nested(UsersJSONSchema, many=True)
    articles = fields.Nested(ArticlesJSONSchema, many=True)
    current_team_record = fields.Nested(TeamRecordsJSONSchema, many=False)
    #matchups = fields.Nested(MatchupsJSONSchema, many=True)

class TeamsListJSONSchema(Schema):
    """Lightweight schema for teams listing - only essential fields"""
    team_id = fields.Int()
    team_name = fields.Str()
    championships = fields.Int()
    sleeper_roster_id = fields.Int()
    current_team_record = fields.Nested(TeamRecordsJSONSchema, many=False)