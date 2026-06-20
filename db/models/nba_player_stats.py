import datetime
from sqlalchemy import Column, Integer, String, DateTime
from db.models.base import Base

class NBAPlayerStats(Base):
    __tablename__ = 'nba_player_stats'
    player_id = Column(Integer, nullable=False, index=True, primary_key=True)
    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)
    team_id = Column(Integer, nullable=False)
    game_id = Column(Integer, nullable=False, index=True, primary_key=True)
    season = Column(Integer, nullable=False, primary_key=True)
    min = Column(String, nullable=True)
    points = Column(Integer, nullable=True)
    pos = Column(String, nullable=True)
    fgm = Column(Integer, nullable=True)
    fga = Column(Integer, nullable=True)
    fgp = Column(String, nullable=True)
    ftm = Column(Integer, nullable=True)
    fta = Column(Integer, nullable=True)
    ftp = Column(String, nullable=True)
    tpm = Column(Integer, nullable=True)
    tpa = Column(Integer, nullable=True)
    tpp = Column(String, nullable=True)
    offReb = Column(Integer, nullable=True)
    defReb = Column(Integer, nullable=True)
    totReb = Column(Integer, nullable=True)
    assists = Column(Integer, nullable=True)
    pFouls = Column(Integer, nullable=True)
    steals = Column(Integer, nullable=True)
    turnovers = Column(Integer, nullable=True)
    blocks = Column(Integer, nullable=True)
    sport_key = Column(String, nullable=False, index=True, primary_key=True)
    commence_time = Column(DateTime, nullable=False)