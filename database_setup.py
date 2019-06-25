import os
import sys
from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, backref
from sqlalchemy import create_engine

Base = declarative_base()

class User(Base):

    __tablename__ = 'user'

    name = Column(String(100), nullable=False)
    id = Column(Integer, primary_key=True)
    picture = Column(String(250))
    email = Column(String(250), nullable=False)
    @property
    def serialize(self):
        return {
            'name': self.name,
            'id': self.id,
            'email': self.email
        }

class Category(Base):
    __tablename__ = 'category'

    name = Column(String(250), nullable=False)
    id = Column(Integer, primary_key=True)

    @property
    def serialize(self):
        return {
            'name': self.name,
            'id': self.id,
        }


class Game(Base):

    __tablename__ = 'game'

    name = Column(String(80), nullable=False)
    id = Column(Integer, primary_key=True)
    description = Column(String(250))
    category_id = Column(Integer, ForeignKey('category.id'))
    category = relationship(Category, backref=backref('game', cascade="all, delete-orphan"))
    user_id = Column(Integer,ForeignKey('user.id'))
    user = relationship(User)

    @property
    def serialize(self):
        return {
            'name': self.name,
            'description': self.description,
            'id': self.id,
        }


# engine = create_engine('sqlite:///catalog.db')
engine = create_engine('postgresql://catalog:password@localhost/catalog')


Base.metadata.create_all(engine)
