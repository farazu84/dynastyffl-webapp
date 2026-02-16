from sqlalchemy.sql.expression import func
from app import db
from app.models.schemas.transactions import TransactionsJSONSchema
from app.models.transaction_rosters import TransactionRosters
from app.league_state_manager import get_current_year


class Transactions(db.Model):
    __tablename__ = 'Transactions'

    transaction_id = db.Column(db.Integer(), primary_key=True, autoincrement=True)

    sleeper_transaction_id = db.Column(db.BigInteger(), nullable=False, unique=True)

    year = db.Column(db.Integer(), nullable=False)

    week = db.Column(db.Integer(), nullable=False)

    type = db.Column(db.Enum('trade', 'waiver', 'free_agent'), nullable=False)

    status = db.Column(db.String(32), nullable=False)

    creator_sleeper_user_id = db.Column(db.BigInteger(), nullable=True)

    sleeper_league_id = db.Column(db.BigInteger(), nullable=False)

    waiver_priority = db.Column(db.Integer(), nullable=True)

    created_at = db.Column(db.DateTime(), nullable=True)

    status_updated_at = db.Column(db.DateTime(), nullable=True)

    # Relationships
    player_moves = db.relationship('TransactionPlayers', back_populates='transaction', lazy='select')
    roster_moves = db.relationship('TransactionRosters', back_populates='transaction', lazy='select')
    draft_pick_moves = db.relationship('TransactionDraftPicks', back_populates='transaction', lazy='select')
    waiver_budget_moves = db.relationship('TransactionWaiverBudget', back_populates='transaction', lazy='select')

    def serialize(self):
        return TransactionsJSONSchema().dump(self)

    @classmethod
    def get_filtered(cls, year=None, week=None, txn_type=None, roster_id=None):
        query = cls.query
        if year:
            query = query.filter_by(year=year)
        if week:
            query = query.filter_by(week=week)
        if txn_type:
            query = query.filter_by(type=txn_type)
        if roster_id:
            query = query.join(TransactionRosters).filter(
                TransactionRosters.sleeper_roster_id == roster_id
            )
        query = query.filter_by(status='complete')
        query = query.order_by(cls.created_at.desc())
        return query.all()

    @classmethod
    def get_by_week(cls, week_number):
        current_year = get_current_year()
        return cls.query \
            .filter_by(week=week_number, year=current_year, status='complete') \
            .order_by(cls.created_at.desc()) \
            .all()

    @classmethod
    def get_for_team(cls, sleeper_roster_id):
        return cls.query \
            .join(TransactionRosters) \
            .filter(TransactionRosters.sleeper_roster_id == sleeper_roster_id) \
            .filter(cls.status == 'complete') \
            .order_by(cls.created_at.desc()) \
            .all()

    @classmethod
    def get_trades_for_team(cls, sleeper_roster_id):
        return cls.query \
            .join(TransactionRosters) \
            .filter(TransactionRosters.sleeper_roster_id == sleeper_roster_id) \
            .filter(cls.type == 'trade') \
            .filter(cls.status == 'complete') \
            .order_by(cls.created_at.desc()) \
            .all()

    @classmethod
    def get_random_trades(cls, limit=5):
        return cls.query \
            .filter_by(type='trade', status='complete') \
            .order_by(func.rand()) \
            .limit(limit) \
            .all()
