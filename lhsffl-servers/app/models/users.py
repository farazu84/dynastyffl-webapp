from .. import db
from sqlalchemy.dialects.mysql import BIGINT
from app.models.schemas.users import UsersJSONSchema

from sqlalchemy.orm import relationship


class Users(db.Model):
    __tablename__ = 'Users'
     
    user_id = db.Column(db.Integer(), nullable=False, primary_key=True)

    user_name = db.Column(db.String(64), nullable=False)

    first_name = db.Column(db.String(64), nullable=False, default='')

    last_name = db.Column(db.String(64), nullable=False, default='')

    sleeper_user_id = db.Column(BIGINT(unsigned=True), nullable=True)

    password = db.Column(db.String(64), nullable=False, default='')

    admin = db.Column(db.Boolean(), nullable=False, default='0')

    team_owner = db.Column(db.Boolean(), nullable=False, default='0')

    owner_groups = db.relationship('TeamOwners', back_populates='user')

    def get_user(self, user_id):
        '''
        Retrieve a user based on id
        '''

        query = 'SELECT first_name FROM Users WHERE user_id = :user_id'

        result = session.query(self).filter(self.user_id==user_id).first()

        return result

    def serialize(self):
        return UsersJSONSchema().dump(self)
