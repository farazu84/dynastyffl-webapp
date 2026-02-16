from marshmallow import Schema, fields


class DraftPicksJSONSchema(Schema):
    draft_pick_id = fields.Int()
    season = fields.Int()
    round = fields.Int()
    pick_no = fields.Int()
    draft_slot = fields.Int()
    drafting_roster_id = fields.Int()
    original_roster_id = fields.Int()
    player_sleeper_id = fields.Int()
    sleeper_draft_id = fields.Int()
    type = fields.Str()
