from marshmallow import Schema, fields


class PlayerWeeklyStatsJSONSchema(Schema):
    player_weekly_stat_id = fields.Int()
    year = fields.Int()
    week = fields.Int()
    sleeper_roster_id = fields.Int()
    player_sleeper_id = fields.Int()
    points = fields.Float()
    is_starter = fields.Bool()
