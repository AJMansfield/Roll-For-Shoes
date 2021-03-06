
from sqlalchemy import Column, BigInteger, String, Integer, ForeignKey, DateTime, UniqueConstraint
from sqlalchemy import create_engine
from sqlalchemy.sql import func
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
import datetime

from keys import keys

engine = create_engine(keys['db-conn'])
Base = declarative_base()

class Player(Base):
    __tablename__ = 'players'

    id = Column(Integer, primary_key=True)

    user_id = Column(BigInteger) # discord user ID
    guild_id = Column(BigInteger) # discord guild ID

    name = Column(String)
    char_id = Column(Integer, ForeignKey('chars.id', ondelete='cascade'))

    created = Column(DateTime(timezone=True), server_default=func.now())
    modified = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.current_timestamp())

    char = relationship('Char', back_populates='players')

class Char(Base):
    __tablename__ = 'chars'

    id = Column(Integer, primary_key=True)

    guild_id = Column(BigInteger) # discord guild ID

    name = Column(String, nullable=False)
    slug = Column(String, nullable=False)
    xp = Column(Integer, nullable=False, server_default='0')

    created = Column(DateTime(timezone=True), server_default=func.now())
    modified = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.current_timestamp())

    players = relationship('Player', back_populates='char', cascade="all, delete", passive_deletes=True)
    skills = relationship('Skill', back_populates='char', cascade="all, delete", passive_deletes=True)

    __table_args__ = (UniqueConstraint('guild_id', 'slug'),)

class Skill(Base):
    __tablename__ = 'skills'

    id = Column(Integer, primary_key=True)

    name = Column(String, nullable=False, server_default='do anything')
    slug = Column(String, nullable=False, server_default='do-anything')
    level = Column(Integer, nullable=False, server_default='1')
    xp = Column(Integer)
    char_id = Column(Integer, ForeignKey('chars.id', ondelete='cascade'), nullable=False)
    parent_id = Column(Integer, ForeignKey('skills.id', ondelete='cascade'))

    created = Column(DateTime(timezone=True), server_default=func.now())
    modified = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.current_timestamp())

    char = relationship('Char', back_populates='skills')
    parent = relationship('Skill', remote_side=[id])
    children = relationship('Skill', remote_side=[parent_id], back_populates='parent', order_by='Skill.created', cascade="all, delete", passive_deletes=True)
    rolls = relationship('Roll', back_populates='skill', cascade="all, delete", passive_deletes=True)
    
    __table_args__ = (UniqueConstraint('char_id', 'slug'),)

class Roll(Base):
    __tablename__ = 'rolls'

    id = Column(Integer, primary_key=True)

    guild_id = Column(BigInteger)
    message_id = Column(BigInteger, nullable=False) # discord message ID to remove reaction from
    channel_id = Column(BigInteger, nullable=False) # discord channel ID to remove reaction from

    skill_id = Column(Integer, ForeignKey('skills.id', ondelete='cascade'), nullable=False)
    token = Column(String(length=1), nullable=False)
    comment = Column(String)

    created = Column(DateTime(timezone=True), server_default=func.now())
    modified = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.current_timestamp())

    skill = relationship('Skill', back_populates='rolls')
    
    __table_args__ = (UniqueConstraint('guild_id', 'token'),)

# class Export(Base):
#     __tablename__ = 'exports'

#     id = Column(Integer, primary_key=True)
#     token = Column(String, nullable=False)
#     char_id = Column(Integer, ForeignKey('chars.id'), nullable=False)

#     created = Column(DateTime(timezone=True), server_default=func.now())
#     modified = Column(DateTime(timezone=True), onupdate=func.now())


    
Base.metadata.create_all(engine)