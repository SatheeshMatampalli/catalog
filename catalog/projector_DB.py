import sys
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, backref
from sqlalchemy import Column, ForeignKey, Integer, String

Base = declarative_base()


class User_Data(Base):
    __tablename__ = 'userdata'
    id = Column(Integer, primary_key=True)
    name = Column(String(75), nullable=False)
    email = Column(String(75), nullable=False)
    picture = Column(String(249))

    @property
    def serialize(self):
        # Object and simple serializeable format
        return {
            'id': self.id,
            'name': self.name,
            'email': self.email,
            'picture': self.picture,
        }


class Brand_Data(Base):
    # This class is to create brand table,
    __tablename__ = 'branddata'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('userdata.id'))
    name = Column(String(75), nullable=False)

    user = relationship(User_Data, backref="branddata")

    @property
    def serialize(self):
        # Object and simple serializeable format
        return {
            'name': self.name,
            'id': self.id,

        }


class Model_Data(Base):
    # This class is to create model table
    __tablename__ = 'modeldata'
    id = Column(Integer, primary_key=True)
    brand_id = Column(Integer, ForeignKey('branddata.id'))
    user_id = Column(Integer, ForeignKey('userdata.id'))
    modelno = Column(String(30))
    colors = Column(String(30))
    cost = Column(String(20))
    description = Column(String(500))

    brandsdata = relationship(Brand_Data, backref=backref('modeldata',
                              cascade='all, delete'))
    usersdata = relationship(User_Data, backref="modeldata")

    @property
    def serialize(self):
        # object and simple serializeable format
        return {

            'id': self.id,

            'modelno': self.modelno,

            'colors':  self.colors,
            'cost': self.cost,
            'description': self.description,


        }

engine = create_engine('sqlite:///projector_databse.db')
Base.metadata.create_all(engine)
