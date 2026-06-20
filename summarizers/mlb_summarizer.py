import logging
from datetime import date, datetime

from interfaces.bettor_index_prop_signals_interface import IBettorIndexPropSignalsService
from interfaces.hit_rates_repository_interface import HitRatesRepositoryInterface
from interfaces.relevant_injury_context_interface import PropInjuryContext, RelevantInjuryContextInterface
from interfaces.summarizer_interface import ISummarizerInterface
from interfaces.venue_last_five_clears_interface import IVenueLastFiveClearsService, VenueLastFiveClearsRequest


logger = logging.getLogger(__name__)


class MLBSummarizer(ISummarizerInterface):
    def __init__(
        self,
        mlb_hit_rates_repository: HitRatesRepositoryInterface,
        relevant_injury_context_service: RelevantInjuryContextInterface | None = None,
        bettor_index_prop_signals_service: IBettorIndexPropSignalsService | None = None,
        venue_last_five_clears_service: IVenueLastFiveClearsService | None = None,
    ):
        self.mlb_hit_rates_repository = mlb_hit_rates_repository
        self.relevant_injury_context_service = relevant_injury_context_service
        self.bettor_index_prop_signals_service = bettor_index_prop_signals_service
        self.venue_last_five_clears_service = venue_last_five_clears_service

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
                "commence_time": self._serialize_datetime(hit_rates[0].commence_time) if hit_rates else None,
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
        summary["venue_last_five_clears"] = self._build_venue_last_five_clears(
            hit_rates,
            market_key,
            outcome_description,
            summary.get("best_over_line"),
            summary.get("best_under_line"),
        )
        summary["relevant_injuries"] = self._get_relevant_injuries(
            hit_rates,
            event_id,
            market_key,
            outcome_description,
        )
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

    def _build_venue_last_five_clears(
        self,
        hit_rates,
        market_key,
        outcome_description,
        best_over_line,
        best_under_line,
    ):
        if not self.venue_last_five_clears_service or not hit_rates:
            return None

        first_hit_rate = hit_rates[0]
        request = VenueLastFiveClearsRequest(
            sport_key=first_hit_rate.sport_key,
            player_id=getattr(first_hit_rate, "player_id", None),
            market_key=market_key,
            outcome_description=outcome_description,
            selected_over_line=best_over_line.get("outcome_line") if best_over_line else None,
            selected_under_line=best_under_line.get("outcome_line") if best_under_line else None,
            player_team_id=getattr(first_hit_rate, "player_team_id", None),
            home_team_id=getattr(first_hit_rate, "home_team_id", None),
            away_team_id=getattr(first_hit_rate, "away_team_id", None),
        )
        payload = self.venue_last_five_clears_service.build(request)

        return payload.to_dict() if payload else None

    def _get_relevant_injuries(self, hit_rates, event_id, market_key, outcome_description):
        if not self.relevant_injury_context_service or not hit_rates:
            return []

        prop_context = self._build_prop_injury_context(
            hit_rates,
            event_id,
            market_key,
            outcome_description,
        )
        relevant_injuries = self.relevant_injury_context_service.get_relevant_injury_context(prop_context)

        return [self._serialize_relevant_injury(injury) for injury in relevant_injuries]

    def _build_prop_injury_context(self, hit_rates, event_id, market_key, outcome_description):
        first_hit_rate = hit_rates[0]
        return PropInjuryContext(
            sport_key=first_hit_rate.sport_key,
            event_id=event_id,
            market_key=market_key,
            outcome_description=outcome_description,
            home_team_id=getattr(first_hit_rate, "home_team_id", None),
            away_team_id=getattr(first_hit_rate, "away_team_id", None),
            player_id=getattr(first_hit_rate, "player_id", None),
            player_team_id=getattr(first_hit_rate, "player_team_id", None),
        )

    def _serialize_relevant_injury(self, relevant_injury):
        return {
            "player_id": relevant_injury.player_id,
            "team_id": relevant_injury.team_id,
            "date": self._serialize_datetime(relevant_injury.date),
            "return_date": self._serialize_datetime(relevant_injury.return_date),
            "display_name": relevant_injury.display_name,
            "position": relevant_injury.position,
            "type": relevant_injury.type,
            "detail": relevant_injury.detail,
            "side": relevant_injury.side,
            "status": relevant_injury.status,
            "long_comment": relevant_injury.long_comment,
            "short_comment": relevant_injury.short_comment,
            "relevance_reason": relevant_injury.relevance_reason,
            "metadata": relevant_injury.metadata,
        }

    def _serialize_datetime(self, value):
        if isinstance(value, datetime):
            return value.isoformat()
        if isinstance(value, date):
            return value.isoformat()
        return value

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