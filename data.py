
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
    char_id = Column(Integer, ForeignKey('chars.id'))

    created = Column(DateTime(timezone=True), server_default=func.now())
    modified = Column(DateTime(timezone=True), onupdate=func.now())

    char = relationship('Char', back_populates='players')

class Char(Base):
    __tablename__ = 'chars'

    id = Column(Integer, primary_key=True)

    guild_id = Column(BigInteger) # discord guild ID

    name = Column(String, nullable=False)
    slug = Column(String, nullable=False, unique=True)
    xp = Column(Integer, nullable=False, server_default='0')

    created = Column(DateTime(timezone=True), server_default=func.now())
    modified = Column(DateTime(timezone=True), onupdate=func.now())

    players = relationship('Player', back_populates='char')
    skills = relationship('Skill', cascade="all,delete", back_populates='char')

    __table_args__ = (UniqueConstraint('guild_id', 'slug'),)

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
    children = relationship('Skill', cascade="all,delete", remote_side=[parent_id], back_populates='parent', order_by='Skill.created')

    __table_args__ = (UniqueConstraint('char_id', 'slug'),)

# class Roll(Base):
#     __tablename__ = 'rolls'

#     id = Column(Integer, primary_key=True)

#     guild_id = Column(BigInteger, ForeignKey('guilds.id'), nullable=False)
#     skill_id = Column(Integer, ForeignKey('skills.id'), nullable=False)
#     message_id = Column(BigInteger) # discord message ID to remove reaction from
#     token = Column(String(length=1))

#     created = Column(DateTime(timezone=True), server_default=func.now())
#     modified = Column(DateTime(timezone=True), onupdate=func.now())

#     guild = relationship('Guild', back_populates='rolls')
#     skill = relationship('Skill')

# class Export(Base):
#     __tablename__ = 'exports'

#     id = Column(Integer, primary_key=True)
#     token = Column(String, nullable=False)
#     char_id = Column(Integer, ForeignKey('chars.id'), nullable=False)

#     created = Column(DateTime(timezone=True), server_default=func.now())
#     modified = Column(DateTime(timezone=True), onupdate=func.now())


    
Base.metadata.create_all(engine)