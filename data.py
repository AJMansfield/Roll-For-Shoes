
from sqlalchemy import Column, BigInteger, String, Integer, ForeignKey, DateTime, create_engine
from sqlalchemy.sql import func
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
import datetime

engine = create_engine('postgresql://postgres:password@localhost/rfs')
Base = declarative_base()

class Player(Base):
    __tablename__ = 'players'

    id = Column(BigInteger, autoincrement=False, primary_key=True)
    name = Column(String)
    char_id = Column(Integer, ForeignKey('chars.id'))
    created = Column(DateTime(timezone=True), server_default=func.now())
    modified = Column(DateTime(timezone=True), onupdate=func.now())

    char = relationship('Char', back_populates='players')

class Char(Base):
    __tablename__ = 'chars'

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    slug = Column(String, nullable=False, unique=True)
    xp = Column(Integer, nullable=False, server_default='0')
    created = Column(DateTime(timezone=True), server_default=func.now())
    modified = Column(DateTime(timezone=True), onupdate=func.now())

    players = relationship('Player', back_populates='char')
    skills = relationship('Skill', back_populates='char')

class Skill(Base):
    __tablename__ = 'skills'

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False, server_default='do anything')
    slug = Column(String, nullable=False, server_default='do-anything')
    level = Column(Integer, nullable=False, server_default='1')
    xp = Column(Integer)
    char_id = Column(Integer, ForeignKey('chars.id'), nullable=False)
    parent_id = Column(Integer, ForeignKey('skills.id'))
    created = Column(DateTime(timezone=True), server_default=func.now())
    modified = Column(DateTime(timezone=True), onupdate=func.now())

    char = relationship('Char', back_populates='skills')
    parent = relationship('Skill', remote_side=[id], back_populates='children')
    children = relationship('Skill', remote_side=[parent_id], back_populates='parent', order_by='Skill.created')

Base.metadata.create_all(engine)