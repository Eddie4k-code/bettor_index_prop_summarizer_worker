from sqlalchemy import Column, Integer, String, Float
from db.models.base import Base
from datetime import datetime

class NBAHitRates(Base):
    __tablename__ = 'nba_hit_rates'
    event_id = Column(String, nullable=False, index=True, primary_key=True)
    bookmaker = Column(String, nullable=False, index=True, primary_key=True)
    market_key = Column(String, nullable=False, index=True, primary_key=True)
    outcome_description = Column(String, nullable=True, primary_key=True)
    outcome_name = Column(String, nullable=False, primary_key=True)
    commence_time = Column(String, nullable=False)
    player_id = Column(Integer, nullable=False, index=True)
    season = Column(Integer, nullable=True)
    sport_key = Column(String, nullable=False, index=True)
    ten_game_hit_rate = Column(Float, nullable=True)
    thirty_game_hit_rate = Column(Float, nullable=True)
    sixty_game_hit_rate = Column(Float, nullable=True)
    outcome_point = Column(String, nullable=False)
    outcome_price = Column(String, nullable=False)
    market_last_update = Column(String, nullable=False)
    home_team = Column(String, nullable=False)
    away_team = Column(String, nullable=False)
    player_team_id = Column(Integer, nullable=True)
    home_team_id = Column(Integer, nullable=True)
    away_team_id = Column(Integer, nullable=True)