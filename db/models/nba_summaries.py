from sqlalchemy import Column, Integer, String, DateTime, Text
from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy.ext.declarative import declarative_base
import datetime

Base = declarative_base()

class NBASummary(Base):
    __tablename__ = "nba_summaries"

    event_id = Column(String, index=True, nullable=False, primary_key=True)
    market_key = Column(String, nullable=True, primary_key=True)
    outcome_description = Column(String, nullable=False, primary_key=True)
    commence_time = Column(DateTime, nullable=False)
    home_team = Column(String, nullable=True)
    away_team = Column(String, nullable=True)
    summary_data = Column(JSON, nullable=False)  # Use Text if not using Postgres
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
