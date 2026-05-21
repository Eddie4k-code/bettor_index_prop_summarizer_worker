from abc import ABC, abstractmethod


class ISummarizerInterface(ABC):
    @abstractmethod
    def summarize(self, market_key: str) -> None:
        pass

    @abstractmethod
    def build_summary(self, hit_rates, event_id, market_key, outcome_description):
        pass

    def find_line_discrepancy(self, hit_rates):
        pass

    def find_odds_discrepancy(self, hit_rates):
        pass

    def find_best_over_line(self, hit_rates):
        pass

    def find_best_under_line(self, hit_rates):
        pass

    def find_best_over_price(self, hit_rates):
        pass

    def find_best_under_price(self, hit_rates):
        pass