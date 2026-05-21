from app import db
from app.models.schemas.nfl_draft_data import NFLDraftDataJSONSchema


class NFLDraftData(db.Model):
    __tablename__ = 'NFLDraftData'
    __table_args__ = (
        db.Index('ix_nfl_draft_data_season', 'nfl_draft_season'),
    )

    nfl_draft_data_id = db.Column(db.Integer(), primary_key=True, autoincrement=True)

    gsis_id = db.Column(db.String(32), nullable=False, unique=True)

    nfl_draft_season = db.Column(db.Integer(), nullable=False)

    round = db.Column(db.Integer(), nullable=False)

    pick = db.Column(db.Integer(), nullable=False)

    drafting_team = db.Column(db.String(8), nullable=False)

    age_at_draft = db.Column(db.Integer(), nullable=True)

    allpro = db.Column(db.Integer(), nullable=False, default=0)

    probowls = db.Column(db.Integer(), nullable=False, default=0)

    seasons_started = db.Column(db.Integer(), nullable=False, default=0)

    career_av = db.Column(db.Integer(), nullable=True)

    weighted_av = db.Column(db.Integer(), nullable=True)

    hof = db.Column(db.Boolean(), nullable=False, default=False)

    def serialize(self):
        return NFLDraftDataJSONSchema().dump(self)
