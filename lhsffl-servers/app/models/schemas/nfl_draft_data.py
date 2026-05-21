from marshmallow import Schema, fields


class NFLDraftDataJSONSchema(Schema):
    nfl_draft_data_id = fields.Int()
    gsis_id = fields.Str()
    nfl_draft_season = fields.Int()
    round = fields.Int()
    pick = fields.Int()
    drafting_team = fields.Str()
    age_at_draft = fields.Int()
    allpro = fields.Int()
    probowls = fields.Int()
    seasons_started = fields.Int()
    career_av = fields.Int()
    weighted_av = fields.Int()
    hof = fields.Bool()
