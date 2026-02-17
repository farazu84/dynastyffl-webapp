from app import db
from app.models.schemas.transaction_players import TransactionPlayersJSONSchema


class TransactionPlayers(db.Model):
    __tablename__ = 'TransactionPlayers'
    __table_args__ = (
        db.Index('ix_txn_players_txn_id', 'transaction_id'),
        db.Index('ix_txn_players_player_id', 'player_sleeper_id'),
    )

    transaction_player_id = db.Column(db.Integer(), primary_key=True, autoincrement=True)

    transaction_id = db.Column(db.Integer(), db.ForeignKey('Transactions.transaction_id'), nullable=False)
    transaction = db.relationship('Transactions', back_populates='player_moves')

    player_sleeper_id = db.Column(db.Integer(), nullable=False)

    sleeper_roster_id = db.Column(db.Integer(), nullable=False)

    team = db.relationship('Teams',
                           foreign_keys=[sleeper_roster_id],
                           primaryjoin='TransactionPlayers.sleeper_roster_id == Teams.sleeper_roster_id',
                           lazy='select')

    player = db.relationship('Players',
                             foreign_keys=[player_sleeper_id],
                             primaryjoin='TransactionPlayers.player_sleeper_id == Players.sleeper_id',
                             lazy='select',
                             viewonly=True)

    action = db.Column(db.Enum('add', 'drop'), nullable=False)

    def serialize(self):
        return TransactionPlayersJSONSchema().dump(self)
