from db.models.base import Base
from sqlalchemy import Column, Integer, String

class Team(Base):
    __tablename__ = 'teams'
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    nickname = Column(String, nullable=True)
    code = Column(String, nullable=True)
    city = Column(String, nullable=True)
    sport_key = Column(String, nullable=False, index=True, primary_key=True)