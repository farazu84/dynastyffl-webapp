from .. import db
from sqlalchemy.dialects.mysql import BIGINT


class TeamOwners(db.Model):
    __tablename__ = 'TeamOwners'

    team_owner_id = db.Column(db.Integer(), nullable=False, primary_key=True)

    user_id = db.Column(db.Integer(), db.ForeignKey('Users.user_id') , nullable=False)
    users = db.relationship('Users')

    sleeper_user_id = db.Column(BIGINT(unsigned=True), nullable=True)

    team_id = db.Column(db.Integer(), db.ForeignKey('Teams.team_id'), nullable=False)
    team = db.relationship('Teams', back_populates='team_owners')

    primary_owner = db.Column(db.Boolean(), nullable=False, default='1')
