from marshmallow import Schema, fields


class PlayerGameLogsJSONSchema(Schema):
    player_game_log_id = fields.Int()
    gsis_id = fields.Str()
    season = fields.Int()
    week = fields.Int()
    team = fields.Str()
    targets = fields.Int()
    receptions = fields.Int()
    rec_air_yards = fields.Float()
    rec_yards = fields.Float()
    rec_touchdowns = fields.Int()
    rush_attempts = fields.Int()
    rush_yards = fields.Float()
    rush_touchdowns = fields.Int()
    pass_touchdowns = fields.Int()
    fantasy_points_actual = fields.Float()
    fantasy_points_expected = fields.Float()
    fantasy_points_diff = fields.Float()
    rec_first_downs = fields.Int()
    rush_first_downs = fields.Int()
