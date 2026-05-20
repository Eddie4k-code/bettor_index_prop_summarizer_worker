from sqlalchemy import Column, String, Integer, Float
from db.models.base import Base

class HitRateSummarizerQueue(Base):
    __tablename__ = 'hit_rate_summarizer_queue'
    event_id = Column(String, nullable=False, index=True, primary_key=True)
    market_key = Column(String, nullable=False, index=True, primary_key=True)
    outcome_description = Column(String, nullable=True, primary_key=True)
    status = Column(String, nullable=False)
    sport_key = Column(String, nullable=False, index=True)