from .. import db
from sqlalchemy.dialects.mysql import BIGINT
from app.models.schemas.users import UsersJSONSchema


class Users(db.Model):
    __tablename__ = 'Users'
     
    user_id = db.Column(db.Integer(), nullable=False, primary_key=True)

    user_name = db.Column(db.String(64), nullable=False)

    first_name = db.Column(db.String(64), nullable=False, default='')

    last_name = db.Column(db.String(64), nullable=False, default='')

    sleeper_user_id = db.Column(BIGINT(unsigned=True), nullable=True)

    email = db.Column(db.String(255), unique=True, nullable=True)

    google_id = db.Column(db.String(255), unique=True, nullable=True)

    password = db.Column(db.String(256), nullable=True, default=None)

    admin = db.Column(db.Boolean(), nullable=False, default=False)

    team_owner = db.Column(db.Boolean(), nullable=False, default=False)

    owner_groups = db.relationship('TeamOwners', back_populates='user')

    def serialize(self):
        return UsersJSONSchema().dump(self)
