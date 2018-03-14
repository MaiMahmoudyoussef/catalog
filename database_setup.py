import sys
from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy import create_engine

Base = declarative_base()

class User(Base):
    __tablename__ = 'user'
    id = Column(Integer, primary_key = True)
    name = Column(String(250), nullable = False)
    email = Column(String(250), nullable = False)
    picture = Column(String(250))

    @property
    def serialize(self):
        #return object data of user
        return {
        'name': self.name,
        'id': self.id,
        'picture': self.picture,
        'emai': self.email,
        }

class Category(Base):
    __tablename__ = 'category'
    id = Column(Integer, primary_key = True)
    name = Column(String(250), nullable = False, unique=True)
    user_id = Column(Integer, ForeignKey('user.id'))
    user = relationship(User)

    @property
    def serialize(self):
        return {
        'name': self.name,
        'id' : self.id,
        'user_id' : self.user_id,
        }

class Item(Base):
    __tablename__ = 'item'
    id = Column(Integer, primary_key = True)
    name = Column(String(250), nullable = False, unique=True)
    description = Column(String(250))
    user_id = Column(Integer, ForeignKey('user.id'))
    user = relationship(User)
    category_id = Column(Integer, ForeignKey('category.id'))
    category = relationship('Category', cascade="all, delete-orphan", single_parent=True)

    @property
    def serialize(self):
        return {
        'name' : self.name,
        'id' : self.id,
        'description' : self.description,
        'user_id' : self.user_id,
        'category_id' : self.category_id,
        }

engine = create_engine(
'sqlite:///catalogitems.db'
)
Base.metadata.create_all(engine)
