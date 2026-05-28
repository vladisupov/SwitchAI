import datetime
import sqlalchemy
from flask_login import UserMixin
from sqlalchemy import orm
from . import __all_models
from data import db_session

from werkzeug.security import generate_password_hash, check_password_hash
from .db_session import SqlAlchemyBase
from sqlalchemy_serializer import SerializerMixin
import secrets


class User(SqlAlchemyBase, UserMixin, SerializerMixin):
    __tablename__ = 'users'

    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True, autoincrement=True)
    email = sqlalchemy.Column(sqlalchemy.String, index=True, unique=True, nullable=True)
    surname = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    name = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    hashed_password = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    modified_date = sqlalchemy.Column(sqlalchemy.DateTime, default=datetime.datetime.now)
    is_verified = sqlalchemy.Column(sqlalchemy.Boolean, default=False)
    verification_token = sqlalchemy.Column(sqlalchemy.String, unique=True)
    token_expires_at = sqlalchemy.Column(sqlalchemy.DateTime, default=datetime.datetime.now)

    responses = orm.relationship("Responses", back_populates='user')

    def generate_verification_token(self):
        self.verification_token = secrets.token_urlsafe(32)
        print(self.verification_token, 1)
        self.token_expires_at = datetime.datetime.now() + datetime.timedelta(days=1)
        print(self.token_expires_at, 1)
        return self.verification_token

    def verify_email(self, token):
        print(token, self.verification_token)
        if self.verification_token == token and self.token_expires_at > datetime.datetime.now():
            self.is_verified = True
            self.verification_token = None
            self.token_expires_at = None
            return True
        return False

    def __repr__(self):
        return f'<User> {self.id} {self.surname} {self.name}'

    def set_password(self, password):
        self.hashed_password = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.hashed_password, password)
