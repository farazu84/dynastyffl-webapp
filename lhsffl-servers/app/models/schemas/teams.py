from marshmallow import Schema, fields
from app.models.schemas.team_owners import TeamOwnersJSONSchema
from app.models.schemas.players import PlayersJSONSchema
from app.models.schemas.users import UsersJSONSchema


class TeamsJSONSchema(Schema):
    team_id = fields.Int()
    team_name = fields.Str()
    championships = fields.Int()
    team_owners = fields.Nested(TeamOwnersJSONSchema, many=True)
    players = fields.Nested(PlayersJSONSchema, many=True)
    roster_size = fields.Int()
    average_age = fields.Float()
    average_starter_age = fields.Float()
    owners = fields.Nested(UsersJSONSchema, many=True)