from app import db
from datetime import datetime
from marshmallow import Schema, fields
from app.models.schemas.sync_status import SyncStatusJSONSchema


class SyncStatus(db.Model):
    __tablename__ = 'SyncStatus'
    
    sync_status_id = db.Column(db.Integer, primary_key=True, autoincrement=True)

    sync_item = db.Column(db.Enum('teams', 'league_state', 'players', 'matchups', 'transactions'), nullable=False)

    timestamp = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    success = db.Column(db.Boolean, nullable=False)

    error = db.Column(db.TEXT, nullable=True)

    def serialize(self):
        return SyncStatusJSONSchema().dump(self)


