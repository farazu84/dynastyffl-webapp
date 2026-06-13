from marshmallow import Schema, fields


class PlayoffMatchupsJSONSchema(Schema):
    playoff_matchup_id = fields.Int()
    year = fields.Int()
    round = fields.Int()
    bracket = fields.Str()
    sleeper_matchup_id = fields.Int()
    sleeper_roster_id = fields.Int(allow_none=True)
    opponent_sleeper_roster_id = fields.Int(allow_none=True)
    winner_sleeper_roster_id = fields.Int(allow_none=True)
    loser_sleeper_roster_id = fields.Int(allow_none=True)
    placement = fields.Int(allow_none=True)
