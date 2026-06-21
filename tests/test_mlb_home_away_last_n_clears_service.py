from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from db.models.mlb_player_stats import MLBPlayerStats

from db.models.base import Base

def build_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine)()
    return session






