from marshmallow import Schema, fields


class BiddingWindowJSONSchema(Schema):
    bidding_window_id = fields.Int()
    year = fields.Int()
    opens_at = fields.DateTime()
    closes_at = fields.DateTime()
    processed = fields.Bool()
    is_open = fields.Bool()
