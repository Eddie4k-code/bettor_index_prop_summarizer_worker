from abc import ABC, abstractmethod


class HitRatesRepositoryInterface(ABC):
        @abstractmethod
        def get_hit_rates_by_keys(self, event_id, market_key, outcome_description) -> list:
            """
            Fetch all NBAHitRates records matching the given (event_id, market_key, outcome_description).
            Returns a list of NBAHitRates model instances.
            """
            pass