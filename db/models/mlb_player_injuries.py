from sqlalchemy import Column, DateTime, Integer, String

from db.models.base import Base

class MLBPlayerInjuries(Base):
    __tablename__ = 'mlb_player_injuries_ball_dont_lie'

    player_id = Column(Integer, nullable=False, index=True, primary_key=True)
    team_id = Column(Integer, nullable=True, index=True, primary_key=True)
    date = Column(DateTime, nullable=True)
    return_date = Column(DateTime, nullable=True)
    display_name = Column(String, nullable=True)
    position = Column(String, nullable=True)
    type = Column(String, nullable=True)
    detail = Column(String, nullable=True)
    side = Column(String, nullable=True)
    status = Column(String, nullable=True)
    long_comment = Column(String, nullable=True)
    short_comment = Column(String, nullable=True)