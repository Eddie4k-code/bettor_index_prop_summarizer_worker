from datetime import datetime
from unittest.mock import MagicMock

from summarizers.mlb_summarizer import MLBSummarizer


class FakeHitRate:
    def __init__(
        self,
        outcome_name,
        outcome_point,
        outcome_price,
        bookmaker,
        commence_time=None,
        ten_game_hit_rate=0,
        thirty_game_hit_rate=0,
        sixty_game_hit_rate=0,
        home_team="NYY",
        away_team="BOS",
        sport_key="baseball_mlb",
    ):
        self.outcome_name = outcome_name
        self.outcome_point = outcome_point
        self.outcome_price = outcome_price
        self.bookmaker = bookmaker
        self.commence_time = commence_time or datetime.now()
        self.ten_game_hit_rate = ten_game_hit_rate
        self.thirty_game_hit_rate = thirty_game_hit_rate
        self.sixty_game_hit_rate = sixty_game_hit_rate
        self.home_team = home_team
        self.away_team = away_team
        self.sport_key = sport_key


def make_summarizer_with_data(hit_rates):
    repo = MagicMock()
    repo.get_hit_rates_by_keys.return_value = hit_rates
    return MLBSummarizer(repo), repo


def test_summarize_returns_none_when_no_hit_rates():
    summarizer, repo = make_summarizer_with_data([])

    summary = summarizer.summarize("evt1", "player_hits", "Aaron Judge")

    assert summary is None
    repo.get_hit_rates_by_keys.assert_called_once_with("evt1", "player_hits", "Aaron Judge")


def test_build_summary_success():
    hit_rates = [
        FakeHitRate("over", 1.5, 105, "FanDuel", ten_game_hit_rate=0.7),
        FakeHitRate("under", 2.5, -102, "DraftKings", ten_game_hit_rate=0.6),
    ]
    summarizer, _ = make_summarizer_with_data(hit_rates)

    summary = summarizer.build_summary(hit_rates, "evt1", "player_hits", "Aaron Judge")

    assert summary["market"] == {
        "market_key": "player_hits",
        "outcome_description": "Aaron Judge",
        "event_id": "evt1",
        "commence_time": hit_rates[0].commence_time,
        "home_team": "NYY",
        "away_team": "BOS",
        "sport_key": "baseball_mlb",
    }
    assert "best_over_line" in summary
    assert "best_under_line" in summary
    assert "best_over_price" in summary
    assert "best_under_price" in summary
    assert "line_discrepancy" in summary
    assert "odds_discrepancy" in summary


def test_line_discrepancy_found():
    hit_rates = [
        FakeHitRate("over", 1.5, 105, "FanDuel"),
        FakeHitRate("over", 2.5, 110, "DraftKings"),
    ]
    summarizer, _ = make_summarizer_with_data(hit_rates)

    result = summarizer.find_line_discrepancy(hit_rates)

    assert result["over"]["discrepancy"] == 1.0
    assert result["over"]["min_line"] == 1.5
    assert result["over"]["max_line"] == 2.5


def test_odds_discrepancy_found():
    hit_rates = [
        FakeHitRate("under", 1.5, -120, "FanDuel"),
        FakeHitRate("under", 1.5, 105, "DraftKings"),
    ]
    summarizer, _ = make_summarizer_with_data(hit_rates)

    result = summarizer.find_odds_discrepancy(hit_rates)

    assert result["under"]["discrepancy"] == 225.0
    assert result["under"]["min_price"] == -120.0
    assert result["under"]["max_price"] == 105.0


def test_best_over_line():
    hit_rates = [
        FakeHitRate("over", 1.5, 100, "FanDuel"),
        FakeHitRate("over", 0.5, 105, "DraftKings"),
    ]
    summarizer, _ = make_summarizer_with_data(hit_rates)

    best = summarizer.identify_best_over_line(hit_rates)

    assert best["outcome_line"] == 0.5
    assert best["bookmaker"] == "DraftKings"


def test_best_under_line():
    hit_rates = [
        FakeHitRate("under", 1.5, 100, "FanDuel"),
        FakeHitRate("under", 2.5, 105, "DraftKings"),
    ]
    summarizer, _ = make_summarizer_with_data(hit_rates)

    best = summarizer.identify_best_under_line(hit_rates)

    assert best["outcome_line"] == 2.5
    assert best["bookmaker"] == "DraftKings"


def test_best_over_price():
    hit_rates = [
        FakeHitRate("over", 1.5, -105, "FanDuel"),
        FakeHitRate("over", 1.5, 110, "DraftKings"),
    ]
    summarizer, _ = make_summarizer_with_data(hit_rates)

    best = summarizer.identify_best_over_price(hit_rates)

    assert best["outcome_price"] == 110.0
    assert best["bookmaker"] == "DraftKings"


def test_best_under_price():
    hit_rates = [
        FakeHitRate("under", 1.5, -110, "FanDuel"),
        FakeHitRate("under", 1.5, 115, "DraftKings"),
    ]
    summarizer, _ = make_summarizer_with_data(hit_rates)

    best = summarizer.identify_best_under_price(hit_rates)

    assert best["outcome_price"] == 115.0
    assert best["bookmaker"] == "DraftKings"