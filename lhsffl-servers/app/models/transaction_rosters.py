from app import db
from app.models.schemas.transaction_rosters import TransactionRostersJSONSchema


class TransactionRosters(db.Model):
    __tablename__ = 'TransactionRosters'

    transaction_roster_id = db.Column(db.Integer(), primary_key=True, autoincrement=True)

    transaction_id = db.Column(db.Integer(), db.ForeignKey('Transactions.transaction_id'), nullable=False)
    transaction = db.relationship('Transactions', back_populates='roster_moves')

    sleeper_roster_id = db.Column(db.Integer(), nullable=False)

    team = db.relationship('Teams',
                           foreign_keys=[sleeper_roster_id],
                           primaryjoin='TransactionRosters.sleeper_roster_id == Teams.sleeper_roster_id',
                           lazy='select')

    is_consenter = db.Column(db.Boolean(), nullable=False, default=False)

    def serialize(self):
        return TransactionRostersJSONSchema().dump(self)
