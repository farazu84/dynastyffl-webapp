from marshmallow import Schema, fields
from app.models.schemas.team_owners import TeamOwnersJSONSchema
from app.models.schemas.players import PlayersJSONSchema

class TeamsJSONSchema(Schema):
    team_id = fields.Int()
    #team_owners = fields.Nested(TeamOwnersJSONSchema, many=True)
    players = fields.Nested(PlayersJSONSchema, many=True)
    team_name = fields.Str()
    #championships = fields.Int()