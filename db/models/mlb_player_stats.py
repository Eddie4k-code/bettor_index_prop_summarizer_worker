from sqlalchemy import Column, DateTime, Integer, String

from db.models.base import Base


class MLBPlayerStats(Base):
    __tablename__ = 'mlb_player_stats_ball_dont_lie'

    player_id = Column(Integer, nullable=False, index=True, primary_key=True)
    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)
    team_name = Column(String, nullable=True)
    game_id = Column(Integer, nullable=False, index=True, primary_key=True)
    season = Column(Integer, nullable=False, primary_key=True)
    at_bats = Column(Integer, nullable=True)
    hits = Column(Integer, nullable=True)
    hr = Column(Integer, nullable=True)
    rbi = Column(Integer, nullable=True)
    bb = Column(Integer, nullable=True)
    k = Column(Integer, nullable=True)
    avg = Column(String, nullable=True)
    obp = Column(String, nullable=True)
    slg = Column(String, nullable=True)
    doubles = Column(Integer, nullable=True)
    triples = Column(Integer, nullable=True)
    stolen_bases = Column(Integer, nullable=True)
    plate_appearances = Column(Integer, nullable=True)
    total_bases = Column(Integer, nullable=True)
    ip = Column(String, nullable=True)
    p_k = Column(Integer, nullable=True)
    p_bb = Column(Integer, nullable=True)
    er = Column(Integer, nullable=True)
    era = Column(String, nullable=True)
    pitch_count = Column(Integer, nullable=True)
    wins = Column(Integer, nullable=True)
    losses = Column(Integer, nullable=True)
    saves = Column(Integer, nullable=True)
    games_started = Column(Integer, nullable=True)
    sport_key = Column(String, nullable=False, index=True, primary_key=True)
    commence_time = Column(DateTime, nullable=False)