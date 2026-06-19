from datetime import date, datetime
import logging

from interfaces.bettor_index_prop_signals_interface import IBettorIndexPropSignalsService
from interfaces.hit_rates_repository_interface import HitRatesRepositoryInterface
from interfaces.summarizer_interface import ISummarizerInterface


logger = logging.getLogger(__name__)

class NBASummarizer(ISummarizerInterface):
    def __init__(
        self,
        nba_hit_rates_repository: HitRatesRepositoryInterface,
        bettor_index_prop_signals_service: IBettorIndexPropSignalsService | None = None,
    ):
        self.nba_hit_rates_repository = nba_hit_rates_repository
        self.bettor_index_prop_signals_service = bettor_index_prop_signals_service

    def summarize(self, event_id, market_key, outcome_description) -> str:
        
        # Get all hit rates by keys
        hit_rates = self.nba_hit_rates_repository.get_hit_rates_by_keys(event_id, market_key, outcome_description)

        if not hit_rates:
            logger.info("No hit rates found for event_id: %s, market_key: %s, outcome_description: %s", event_id, market_key, outcome_description)
            return None

        summary = self.build_summary(hit_rates, event_id, market_key, outcome_description)

        return summary

    def build_summary(self, hit_rates, event_id, market_key, outcome_description):
        summary = {}

        logging.info("Building summary for event_id: %s, market_key: %s, outcome_description: %s with %d hit rates", event_id, market_key, outcome_description, len(hit_rates))

        summary["market"] = {
            "market_key": market_key,
            "outcome_description": outcome_description,
            "event_id": event_id,
            "commence_time": self._serialize_datetime(hit_rates[0].commence_time) if hit_rates else None,
            "home_team": hit_rates[0].home_team if hit_rates else None,
            "away_team": hit_rates[0].away_team if hit_rates else None,
            "sport_key": hit_rates[0].sport_key if hit_rates else None
        }
        summary["best_over_line"] = self.identify_best_over_line(hit_rates)
        summary["best_under_line"] = self.identify_best_under_line(hit_rates)
        summary["best_over_price"] = self.identify_best_over_price(hit_rates)
        summary["best_under_price"] = self.identify_best_under_price(hit_rates)

        # Add line discrepancy
        summary["line_discrepancy"] = self.find_line_discrepancy(hit_rates)
        # Add odds discrepancy
        summary["odds_discrepancy"] = self.find_odds_discrepancy(hit_rates)
        summary["bettorindexpropsignals"] = self._build_bettor_index_prop_signals(summary)

        return summary

    def _build_bettor_index_prop_signals(self, summary):
        if not self.bettor_index_prop_signals_service:
            return {}

        return self.bettor_index_prop_signals_service.build_signal(
            best_over_line=summary.get("best_over_line"),
            best_under_line=summary.get("best_under_line"),
            best_over_price=summary.get("best_over_price"),
            best_under_price=summary.get("best_under_price"),
            line_discrepancy_over=summary.get("line_discrepancy", {}).get("over"),
        )

    def _serialize_datetime(self, value):
        if isinstance(value, datetime):
            return value.isoformat()
        if isinstance(value, date):
            return value.isoformat()
        return value

    def find_line_discrepancy(self, hit_rates):
        # For both over and under
        result = {}
        for outcome in ["over", "under"]:
            lines = [(float(hr.outcome_point), hr.bookmaker) for hr in hit_rates if hr.outcome_name == outcome]
            if not lines:
                result[outcome] = "No data"
                continue
            min_line, min_book = min(lines, key=lambda x: x[0])
            max_line, max_book = max(lines, key=lambda x: x[0])
            if min_line != max_line:
                result[outcome] = {
                    "discrepancy": round(abs(max_line - min_line), 2),
                    "min_line": min_line,
                    "min_book": min_book,
                    "max_line": max_line,
                    "max_book": max_book
                }
            else:
                result[outcome] = "No line discrepancy"
        return result

    def find_odds_discrepancy(self, hit_rates):
        # For both over and under
        result = {}
        for outcome in ["over", "under"]:
            prices = [(float(hr.outcome_price), hr.bookmaker) for hr in hit_rates if hr.outcome_name == outcome]
            if not prices:
                result[outcome] = "No data"
                continue
            min_price, min_book = min(prices, key=lambda x: x[0])
            max_price, max_book = max(prices, key=lambda x: x[0])
            if min_price != max_price:
                result[outcome] = {
                    "discrepancy": round(abs(max_price - min_price), 2),
                    "min_price": min_price,
                    "min_book": min_book,
                    "max_price": max_price,
                    "max_book": max_book
                }
            else:
                result[outcome] = "No odds discrepancy"
        return result

    def identify_best_over_line(self, hit_rates):
        over_rates = [hr for hr in hit_rates if hr.outcome_name == "over"]
        if not over_rates:
            logger.info("No over hit rates found for event_id: %s, market_key: %s, outcome_description: %s", hit_rates[0].event_id if hit_rates else "N/A", hit_rates[0].market_key if hit_rates else "N/A", hit_rates[0].outcome_description if hit_rates else "N/A")
        best = over_rates[0] if over_rates else None
        best_over_line = {
            "bookmaker": best.bookmaker if best.bookmaker else None,
            "outcome_line": float(best.outcome_point) if best.outcome_point else None,  # Start with highest possible, look for lowest
            "ten_game_hit_rate": best.ten_game_hit_rate if best.ten_game_hit_rate and best.ten_game_hit_rate is not None else None,
            "thirty_game_hit_rate": best.thirty_game_hit_rate if best and best.thirty_game_hit_rate is not None else None,
            "sixty_game_hit_rate": best.sixty_game_hit_rate if best and best.sixty_game_hit_rate is not None else None
        }

        for hr in over_rates:
            if hr.outcome_name == "over" and float(hr.outcome_point) < best_over_line["outcome_line"]:
                best_over_line["bookmaker"] = hr.bookmaker
                best_over_line["outcome_line"] = float(hr.outcome_point)
                best_over_line["ten_game_hit_rate"] = hr.ten_game_hit_rate
                best_over_line["thirty_game_hit_rate"] = hr.thirty_game_hit_rate
                best_over_line["sixty_game_hit_rate"] = hr.sixty_game_hit_rate

        return best_over_line


    def identify_best_under_line(self, hit_rates):
        under_rates = [hr for hr in hit_rates if hr.outcome_name == "under"]
        if not under_rates:
            logger.info("No under hit rates found for event_id: %s, market_key: %s, outcome_description: %s", hit_rates[0].event_id if hit_rates else "N/A", hit_rates[0].market_key if hit_rates else "N/A", hit_rates[0].outcome_description if hit_rates else "N/A")
        best = under_rates[0] if under_rates else None
        
        best_under_line = {
            "bookmaker": best.bookmaker if best and best.bookmaker else None,
            "outcome_line": float(best.outcome_point) if best and best.outcome_point else None,  # Start with highest possible, look for lowest
            "ten_game_hit_rate": best.ten_game_hit_rate if best and best.ten_game_hit_rate is not None else None,
            "thirty_game_hit_rate": best.thirty_game_hit_rate if best and best.thirty_game_hit_rate is not None else None,
            "sixty_game_hit_rate": best.sixty_game_hit_rate if best and best.sixty_game_hit_rate is not None else None
        }

        for hr in under_rates:
            if hr.outcome_name == "under" and float(hr.outcome_point) > best_under_line["outcome_line"]:
                best_under_line["bookmaker"] = hr.bookmaker
                best_under_line["outcome_line"] = float(hr.outcome_point)
                best_under_line["ten_game_hit_rate"] = hr.ten_game_hit_rate
                best_under_line["thirty_game_hit_rate"] = hr.thirty_game_hit_rate
                best_under_line["sixty_game_hit_rate"] = hr.sixty_game_hit_rate

        return best_under_line

    def identify_best_over_price(self, hit_rates):
        over_rates = [hr for hr in hit_rates if hr.outcome_name == "over"]
        if not over_rates:
            logger.info("No over hit rates found for event_id: %s, market_key: %s, outcome_description: %s", hit_rates[0].event_id if hit_rates else "N/A", hit_rates[0].market_key if hit_rates else "N/A", hit_rates[0].outcome_description if hit_rates else "N/A")
            return None
        best = over_rates[0] if over_rates else None
        best_over_price = {
            "bookmaker": best.bookmaker if best and best.bookmaker else None,
            "outcome_price": float(best.outcome_price) if best and best.outcome_price else None,
            "ten_game_hit_rate": best.ten_game_hit_rate if best and best.ten_game_hit_rate is not None else None,
            "thirty_game_hit_rate": best.thirty_game_hit_rate if best and best.thirty_game_hit_rate is not None else None,
            "sixty_game_hit_rate": best.sixty_game_hit_rate if best and best.sixty_game_hit_rate is not None else None
        }

        for hr in over_rates:
            if hr.outcome_name == "over" and float(hr.outcome_price) > float(best_over_price["outcome_price"]):
                best_over_price["bookmaker"] = hr.bookmaker
                best_over_price["outcome_price"] = float(hr.outcome_price)
                best_over_price["ten_game_hit_rate"] = hr.ten_game_hit_rate
                best_over_price["thirty_game_hit_rate"] = hr.thirty_game_hit_rate
                best_over_price["sixty_game_hit_rate"] = hr.sixty_game_hit_rate

        return best_over_price
    

    def identify_best_under_price(self, hit_rates):
        under_rates = [hr for hr in hit_rates if hr.outcome_name == "under"]
        if not under_rates:
            logger.info("No under hit rates found for event_id: %s, market_key: %s, outcome_description: %s", hit_rates[0].event_id if hit_rates else "N/A", hit_rates[0].market_key if hit_rates else "N/A", hit_rates[0].outcome_description if hit_rates else "N/A")
        best = under_rates[0] if under_rates else None
        best_under_price = {
            "bookmaker": best.bookmaker if best and best.bookmaker else None,
            "outcome_price": float(best.outcome_price) if best and best.outcome_price else None,
            "ten_game_hit_rate": best.ten_game_hit_rate if best and best.ten_game_hit_rate is not None else None,
            "thirty_game_hit_rate": best.thirty_game_hit_rate if best and best.thirty_game_hit_rate is not None else None,
            "sixty_game_hit_rate": best.sixty_game_hit_rate if best and best.sixty_game_hit_rate is not None else None
        }

        for hr in under_rates:
            if hr.outcome_name == "under" and float(hr.outcome_price) > float(best_under_price["outcome_price"]):
                best_under_price["bookmaker"] = hr.bookmaker
                best_under_price["outcome_price"] = float(hr.outcome_price)
                best_under_price["ten_game_hit_rate"] = hr.ten_game_hit_rate
                best_under_price["thirty_game_hit_rate"] = hr.thirty_game_hit_rate
                best_under_price["sixty_game_hit_rate"] = hr.sixty_game_hit_rate

        return best_under_price




