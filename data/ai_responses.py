import datetime
import sqlalchemy
from flask_login import UserMixin
from sqlalchemy import orm
from .db_session import SqlAlchemyBase
from sqlalchemy_serializer import SerializerMixin
from . import __all_models


class Responses(SqlAlchemyBase, UserMixin, SerializerMixin):
    __tablename__ = 'ai_responses'
    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True, autoincrement=True)
    user_id = sqlalchemy.Column(sqlalchemy.Integer, sqlalchemy.ForeignKey('users.id'))
    model = sqlalchemy.Column(sqlalchemy.String)
    prompt = sqlalchemy.Column(sqlalchemy.String)
    response = sqlalchemy.Column(sqlalchemy.String)
    response_date = sqlalchemy.Column(sqlalchemy.DateTime, default=datetime.datetime.now)

    user = orm.relationship('User')

    def __repr__(self):
        return f'<Response> {self.id} {self.model} {self.prompt} {self.response}'