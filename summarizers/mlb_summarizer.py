import logging

from interfaces.hit_rates_repository_interface import HitRatesRepositoryInterface
from interfaces.summarizer_interface import ISummarizerInterface


logger = logging.getLogger(__name__)


class MLBSummarizer(ISummarizerInterface):
    def __init__(self, mlb_hit_rates_repository: HitRatesRepositoryInterface):
        self.mlb_hit_rates_repository = mlb_hit_rates_repository

    def summarize(self, event_id, market_key, outcome_description):
        hit_rates = self.mlb_hit_rates_repository.get_hit_rates_by_keys(event_id, market_key, outcome_description)

        if not hit_rates:
            logger.info(
                "No hit rates found for event_id: %s, market_key: %s, outcome_description: %s",
                event_id,
                market_key,
                outcome_description,
            )
            return None

        return self.build_summary(hit_rates, event_id, market_key, outcome_description)

    def build_summary(self, hit_rates, event_id, market_key, outcome_description):
        summary = {
            "market": {
                "market_key": market_key,
                "outcome_description": outcome_description,
                "event_id": event_id,
                "commence_time": hit_rates[0].commence_time if hit_rates else None,
                "home_team": hit_rates[0].home_team if hit_rates else None,
                "away_team": hit_rates[0].away_team if hit_rates else None,
                "sport_key": hit_rates[0].sport_key if hit_rates else None,
            }
        }
        summary["best_over_line"] = self.identify_best_over_line(hit_rates)
        summary["best_under_line"] = self.identify_best_under_line(hit_rates)
        summary["best_over_price"] = self.identify_best_over_price(hit_rates)
        summary["best_under_price"] = self.identify_best_under_price(hit_rates)
        summary["line_discrepancy"] = self.find_line_discrepancy(hit_rates)
        summary["odds_discrepancy"] = self.find_odds_discrepancy(hit_rates)

        return summary

    def find_line_discrepancy(self, hit_rates):
        result = {}
        for outcome in ["over", "under"]:
            lines = [(float(hr.outcome_point), hr.bookmaker) for hr in hit_rates if hr.outcome_name == outcome]
            if not lines:
                result[outcome] = "No data"
                continue

            min_line, min_book = min(lines, key=lambda line: line[0])
            max_line, max_book = max(lines, key=lambda line: line[0])
            if min_line != max_line:
                result[outcome] = {
                    "discrepancy": round(abs(max_line - min_line), 2),
                    "min_line": min_line,
                    "min_book": min_book,
                    "max_line": max_line,
                    "max_book": max_book,
                }
            else:
                result[outcome] = "No line discrepancy"

        return result

    def find_odds_discrepancy(self, hit_rates):
        result = {}
        for outcome in ["over", "under"]:
            prices = [(float(hr.outcome_price), hr.bookmaker) for hr in hit_rates if hr.outcome_name == outcome]
            if not prices:
                result[outcome] = "No data"
                continue

            min_price, min_book = min(prices, key=lambda price: price[0])
            max_price, max_book = max(prices, key=lambda price: price[0])
            if min_price != max_price:
                result[outcome] = {
                    "discrepancy": round(abs(max_price - min_price), 2),
                    "min_price": min_price,
                    "min_book": min_book,
                    "max_price": max_price,
                    "max_book": max_book,
                }
            else:
                result[outcome] = "No odds discrepancy"

        return result

    def identify_best_over_line(self, hit_rates):
        over_rates = [hr for hr in hit_rates if hr.outcome_name == "over"]
        if not over_rates:
            return None

        best = min(over_rates, key=lambda hit_rate: float(hit_rate.outcome_point))
        return self._line_payload(best)

    def identify_best_under_line(self, hit_rates):
        under_rates = [hr for hr in hit_rates if hr.outcome_name == "under"]
        if not under_rates:
            return None

        best = max(under_rates, key=lambda hit_rate: float(hit_rate.outcome_point))
        return self._line_payload(best)

    def identify_best_over_price(self, hit_rates):
        over_rates = [hr for hr in hit_rates if hr.outcome_name == "over"]
        if not over_rates:
            return None

        best = max(over_rates, key=lambda hit_rate: float(hit_rate.outcome_price))
        return self._price_payload(best)

    def identify_best_under_price(self, hit_rates):
        under_rates = [hr for hr in hit_rates if hr.outcome_name == "under"]
        if not under_rates:
            return None

        best = max(under_rates, key=lambda hit_rate: float(hit_rate.outcome_price))
        return self._price_payload(best)

    def _line_payload(self, hit_rate):
        return {
            "bookmaker": hit_rate.bookmaker,
            "outcome_line": float(hit_rate.outcome_point),
            "ten_game_hit_rate": hit_rate.ten_game_hit_rate,
            "thirty_game_hit_rate": hit_rate.thirty_game_hit_rate,
            "sixty_game_hit_rate": hit_rate.sixty_game_hit_rate,
        }

    def _price_payload(self, hit_rate):
        return {
            "bookmaker": hit_rate.bookmaker,
            "outcome_price": float(hit_rate.outcome_price),
            "ten_game_hit_rate": hit_rate.ten_game_hit_rate,
            "thirty_game_hit_rate": hit_rate.thirty_game_hit_rate,
            "sixty_game_hit_rate": hit_rate.sixty_game_hit_rate,
        }