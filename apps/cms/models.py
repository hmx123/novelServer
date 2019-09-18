from datetime import datetime

from werkzeug.security import generate_password_hash, check_password_hash

from exts import db


class CMSUser(db.Model):
    __tablename__ = 'cms_user'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String(50),nullable=True)
    _password = db.Column(db.String(100),nullable=True)
    email = db.Column(db.String(50), nullable=True)
    join_time = db.Column(db.DATETIME, default=datetime.now)

    def __init__(self, username, password, email):
        self.username = username
        self.password = password
        self.email = email

    @property
    def password(self):
        return self._password

    @password.setter
    def password(self, rew_password):
        self._password = generate_password_hash(rew_password)

    def check_password(self, rew_password):
        result = check_password_hash(self.password, rew_password)
        return result



