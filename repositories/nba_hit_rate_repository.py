from typing import List, Tuple
from sqlalchemy.orm import Session
from db.models.nba_hit_rates import NBAHitRates
from interfaces.hit_rates_repository_interface import HitRatesRepositoryInterface

class NBAHitRatesRepository(HitRatesRepositoryInterface):
    def __init__(self, db: Session):
        self.db = db

    def get_hit_rates_by_keys(self, event_id, market_key, outcome_description) -> List[NBAHitRates]:
        
        return (
            self.db.query(NBAHitRates)
            .filter(
                NBAHitRates.event_id == event_id,
                NBAHitRates.market_key == market_key,
                NBAHitRates.outcome_description == outcome_description
            )
            .all()
        )

