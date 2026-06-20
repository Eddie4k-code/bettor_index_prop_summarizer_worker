from db.models.base import Base
from sqlalchemy import Column, Integer, String, DateTime, Float

class Game(Base):
    __tablename__ = 'games'
    id = Column(Integer, primary_key=True)
    season = Column(Integer, nullable=False, primary_key=True)
    date = Column(DateTime, nullable=False)
    status = Column(String, nullable=False)
    home_team = Column(String, nullable=False, primary_key=True)
    home_team_id = Column(Integer, nullable=False, primary_key=True)
    away_team = Column(String, nullable=False, primary_key=True)
    away_team_id = Column(Integer, nullable=False, primary_key=True)
    home_team_score = Column(Integer, nullable=False)
    away_team_score = Column(Integer, nullable=False)
    sport_key = Column(String, nullable=False, primary_key=True)