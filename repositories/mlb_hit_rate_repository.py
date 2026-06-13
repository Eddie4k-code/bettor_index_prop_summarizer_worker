from typing import List

from sqlalchemy.orm import Session

from db.models.mlb_hit_rates import MLBHitRates
from interfaces.hit_rates_repository_interface import HitRatesRepositoryInterface


class MLBHitRatesRepository(HitRatesRepositoryInterface):
    def __init__(self, db: Session):
        self.db = db

    def get_hit_rates_by_keys(self, event_id, market_key, outcome_description) -> List[MLBHitRates]:
        return (
            self.db.query(MLBHitRates)
            .filter(
                MLBHitRates.event_id == event_id,
                MLBHitRates.market_key == market_key,
                MLBHitRates.outcome_description == outcome_description,
            )
            .all()
        )