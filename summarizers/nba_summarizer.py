from collections import defaultdict

from interfaces.summarizer_interface import ISummarizerInterface
from interfaces.hit_rates_repository_interface import HitRatesRepositoryInterface
from datetime import datetime

class NBASummarizer(ISummarizerInterface):
    def __init__(self,nba_hit_rates_repository: HitRatesRepositoryInterface):
        self.nba_hit_rates_repository = nba_hit_rates_repository

    def summarize(self, event_id, market_key, outcome_description) -> str:
        
        # Get all hit rates by keys
        hit_rates = self.nba_hit_rates_repository.get_hit_rates_by_keys(event_id, market_key, outcome_description)

        summaries = self.build_summary(hit_rates)

    def build_summary(self, hit_rates, event_id, market_key, outcome_description):
        summary = {}

        summary["market"] = {
            "market_key": market_key,
            "outcome_description": outcome_description,
            "event_id": event_id,
            "commence_time": hit_rates[0].commence_time if hit_rates else None,
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

        return summary

    def find_line_discrepancy(self, hit_rates):
        # For both over and under
        result = {}
        for outcome in ["over", "under"]:
            lines = [(hr.outcome_line, hr.bookmaker) for hr in hit_rates if hr.outcome_name == outcome]
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
            prices = [(hr.outcome_price, hr.bookmaker) for hr in hit_rates if hr.outcome_name == outcome]
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
        best_over_line = {
            "bookmaker": None,
            "outcome_line": float('inf'),  # Start with highest possible, look for lowest
            "ten_game_hit_rate": 0,
            "twenty_game_hit_rate": 0,
            "thirty_game_hit_rate": 0
        }

        for hr in hit_rates:
            if hr.outcome_name == "over" and hr.outcome_line < best_over_line["outcome_line"]:
                best_over_line["bookmaker"] = hr.bookmaker
                best_over_line["outcome_line"] = hr.outcome_line
                best_over_line["ten_game_hit_rate"] = hr.ten_game_hit_rate
                best_over_line["twenty_game_hit_rate"] = hr.twenty_game_hit_rate
                best_over_line["thirty_game_hit_rate"] = hr.thirty_game_hit_rate

        return best_over_line


    def identify_best_under_line(self, hit_rates):
        best_under_line = {
            "bookmaker": None,
            "outcome_line": float('-inf'),
            "ten_game_hit_rate": 0,
            "twenty_game_hit_rate": 0,
            "thirty_game_hit_rate": 0
        }

        for hr in hit_rates:
            if hr.outcome_name == "under" and hr.outcome_line > best_under_line["outcome_line"]:
                best_under_line["bookmaker"] = hr.bookmaker
                best_under_line["outcome_line"] = hr.outcome_line
                best_under_line["ten_game_hit_rate"] = hr.ten_game_hit_rate
                best_under_line["twenty_game_hit_rate"] = hr.twenty_game_hit_rate
                best_under_line["thirty_game_hit_rate"] = hr.thirty_game_hit_rate

        return best_under_line

    def identify_best_over_price(self, hit_rates):
        best_over_price = {
            "bookmaker": None,
            "outcome_price": float('-inf'),
            "ten_game_hit_rate": 0,
            "twenty_game_hit_rate": 0,
            "thirty_game_hit_rate": 0
        }

        for hr in hit_rates:
            if hr.outcome_name == "over" and hr.outcome_price > best_over_price["outcome_price"]:
                best_over_price["bookmaker"] = hr.bookmaker
                best_over_price["outcome_price"] = hr.outcome_price
                best_over_price["ten_game_hit_rate"] = hr.ten_game_hit_rate
                best_over_price["twenty_game_hit_rate"] = hr.twenty_game_hit_rate
                best_over_price["thirty_game_hit_rate"] = hr.thirty_game_hit_rate

        return best_over_price
    

    def identify_best_under_price(self, hit_rates):
        best_under_price = {
            "bookmaker": None,
            "outcome_price": float('-inf'),
            "ten_game_hit_rate": 0,
            "twenty_game_hit_rate": 0,
            "thirty_game_hit_rate": 0
        }

        for hr in hit_rates:
            if hr.outcome_name == "under" and hr.outcome_price > best_under_price["outcome_price"]:
                best_under_price["bookmaker"] = hr.bookmaker
                best_under_price["outcome_price"] = hr.outcome_price
                best_under_price["ten_game_hit_rate"] = hr.ten_game_hit_rate
                best_under_price["twenty_game_hit_rate"] = hr.twenty_game_hit_rate
                best_under_price["thirty_game_hit_rate"] = hr.thirty_game_hit_rate

        return best_under_price




