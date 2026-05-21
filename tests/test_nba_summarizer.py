import pytest
from summarizers.nba_summarizer import NBASummarizer
from unittest.mock import MagicMock
from datetime import datetime

class FakeHitRate:
    def __init__(self, outcome_name, outcome_line, outcome_price, bookmaker, commence_time=None,
                 ten_game_hit_rate=0, twenty_game_hit_rate=0, thirty_game_hit_rate=0):
        self.outcome_name = outcome_name
        self.outcome_line = outcome_line
        self.outcome_price = outcome_price
        self.bookmaker = bookmaker
        self.commence_time = commence_time or datetime.now()
        self.ten_game_hit_rate = ten_game_hit_rate
        self.twenty_game_hit_rate = twenty_game_hit_rate
        self.thirty_game_hit_rate = thirty_game_hit_rate

def make_summarizer_with_data(hit_rates):
    repo = MagicMock()
    repo.get_hit_rates_by_keys.return_value = hit_rates
    return NBASummarizer(repo)

def test_build_summary_success(mocker):
    hit_rates = [
        FakeHitRate("over", 12.5, 105, "FanDuel", ten_game_hit_rate=0.7),
        FakeHitRate("under", 14.5, -102, "DraftKings", ten_game_hit_rate=0.6),
    ]
    summarizer = make_summarizer_with_data(hit_rates)
    summary = summarizer.build_summary(hit_rates, 1, "player_points", "Over/Under")
    assert "market" in summary
    assert "best_over_line" in summary
    assert "best_under_line" in summary
    assert "line_discrepancy" in summary
    assert "odds_discrepancy" in summary

def test_line_discrepancy_found():
    hit_rates = [
        FakeHitRate("over", 12.5, 105, "FanDuel"),
        FakeHitRate("over", 14.5, 110, "DraftKings"),
    ]
    summarizer = make_summarizer_with_data(hit_rates)
    result = summarizer.find_line_discrepancy(hit_rates)
    assert result["over"]["discrepancy"] == 2.0
    assert result["over"]["min_line"] == 12.5
    assert result["over"]["max_line"] == 14.5

def test_no_line_discrepancy():
    hit_rates = [
        FakeHitRate("over", 12.5, 105, "FanDuel"),
        FakeHitRate("over", 12.5, 110, "DraftKings"),
    ]
    summarizer = make_summarizer_with_data(hit_rates)
    result = summarizer.find_line_discrepancy(hit_rates)
    assert result["over"] == "No line discrepancy"

def test_best_under_line():
    hit_rates = [
        FakeHitRate("under", 13.5, 100, "FanDuel"),
        FakeHitRate("under", 14.5, 105, "DraftKings"),
    ]
    summarizer = make_summarizer_with_data(hit_rates)
    best = summarizer.identify_best_under_line(hit_rates)
    assert best["outcome_line"] == 14.5
    assert best["bookmaker"] == "DraftKings"

def test_best_over_line():
    hit_rates = [
        FakeHitRate("over", 12.5, 100, "FanDuel"),
        FakeHitRate("over", 11.5, 105, "DraftKings"),
    ]
    summarizer = make_summarizer_with_data(hit_rates)
    best = summarizer.identify_best_over_line(hit_rates)
    assert best["outcome_line"] == 11.5
    assert best["bookmaker"] == "DraftKings"

def test_best_under_price():
    hit_rates = [
        FakeHitRate("under", 13.5, 100, "FanDuel"),
        FakeHitRate("under", 13.5, 110, "DraftKings"),
    ]
    summarizer = make_summarizer_with_data(hit_rates)
    best = summarizer.identify_best_under_price(hit_rates)
    assert best["outcome_price"] == 110
    assert best["bookmaker"] == "DraftKings"

def test_best_over_price():
    hit_rates = [
        FakeHitRate("over", 12.5, 100, "FanDuel"),
        FakeHitRate("over", 12.5, 120, "DraftKings"),
    ]
    summarizer = make_summarizer_with_data(hit_rates)
    best = summarizer.identify_best_over_price(hit_rates)
    assert best["outcome_price"] == 120
    assert best["bookmaker"] == "DraftKings"

def test_odds_discrepancy_found():
    hit_rates = [
        FakeHitRate("over", 12.5, 100, "FanDuel"),
        FakeHitRate("over", 12.5, 120, "DraftKings"),
    ]
    summarizer = make_summarizer_with_data(hit_rates)
    result = summarizer.find_odds_discrepancy(hit_rates)
    assert result["over"]["discrepancy"] == 20
    assert result["over"]["min_price"] == 100
    assert result["over"]["max_price"] == 120

def test_no_odds_discrepancy():
    hit_rates = [
        FakeHitRate("over", 12.5, 100, "FanDuel"),
        FakeHitRate("over", 12.5, 100, "DraftKings"),
    ]
    summarizer = make_summarizer_with_data(hit_rates)
    result = summarizer.find_odds_discrepancy(hit_rates)
    assert result["over"] == "No odds discrepancy"
