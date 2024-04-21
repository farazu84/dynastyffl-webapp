from .. import db


class Users(db.Model):
    __tablename__ = 'Users'
     
    user_id = db.Column(db.Integer(), primary_key=True)

    first_name = db.Column(db.String(64))

    last_name = db.Column(db.String(64))

    def get_user(self, user_id):
        '''
        Retrieve a user based on id
        '''

        query = 'SELECT first_name FROM Users WHERE user_id = :user_id'

        result = session.query(self).filter(self.user_id==user_id).first()

        return result

    def serialize(self):
        return {
            'user_id': self.user_id,
            'first_name': self.first_name,
            'last_name': self.last_name
        }