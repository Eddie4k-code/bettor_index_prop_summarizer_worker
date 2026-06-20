import pytest
from summarizers.nba_summarizer import NBASummarizer
from unittest.mock import MagicMock
from datetime import datetime
from types import SimpleNamespace

from interfaces.venue_last_five_clears_interface import VenueLastFiveClears, VenueLastFiveClearsSide
from services.nba_venue_last_five_clears_service import NBAVenueLastFiveClearsService


class FakeHitRate:
    def __init__(self, outcome_name, outcome_line, outcome_price, bookmaker, commence_time=None,
                 ten_game_hit_rate=0, twenty_game_hit_rate=0, thirty_game_hit_rate=0,
                 sixty_game_hit_rate=0, home_team="LAL", away_team="BOS", sport_key="basketball_nba",
                 player_id=123, player_team_id=10, home_team_id=10, away_team_id=20):
        self.outcome_name = outcome_name
        self.outcome_line = outcome_line
        self.outcome_point = outcome_line
        self.outcome_price = outcome_price
        self.bookmaker = bookmaker
        self.commence_time = commence_time or datetime.now()
        self.ten_game_hit_rate = ten_game_hit_rate
        self.twenty_game_hit_rate = twenty_game_hit_rate
        self.thirty_game_hit_rate = thirty_game_hit_rate
        self.sixty_game_hit_rate = sixty_game_hit_rate
        self.home_team = home_team
        self.away_team = away_team
        self.sport_key = sport_key
        self.player_id = player_id
        self.player_team_id = player_team_id
        self.home_team_id = home_team_id
        self.away_team_id = away_team_id

def make_summarizer_with_data(hit_rates):
    repo = MagicMock()
    repo.get_hit_rates_by_keys.return_value = hit_rates
    signal_service = MagicMock()
    signal_service.build_signal.return_value = {
        "side": "OVER",
        "strength": "medium",
        "action": "shop_price",
        "lean_label": "Lean Over",
        "market_label": "Worth Watching",
        "reason_text": "Backend sees a clear over trend, but the current market is not strong enough yet.",
    }
    venue_service = MagicMock()
    venue_service.build.return_value = None
    return NBASummarizer(repo, signal_service, venue_service), venue_service

def test_build_summary_success(mocker):
    hit_rates = [
        FakeHitRate("over", 12.5, 105, "FanDuel", ten_game_hit_rate=0.7, home_team="NYK", away_team="BKN", sport_key="nba"),
        FakeHitRate("under", 14.5, -102, "DraftKings", ten_game_hit_rate=0.6, home_team="NYK", away_team="BKN", sport_key="nba"),
    ]
    summarizer, venue_service = make_summarizer_with_data(hit_rates)
    summary = summarizer.build_summary(hit_rates, 1, "player_points", "Over/Under")
    assert "market" in summary
    assert "best_over_line" in summary
    assert "best_under_line" in summary
    assert "line_discrepancy" in summary
    assert "odds_discrepancy" in summary
    assert summary["venue_last_five_clears"] is None
    assert summary["market"]["commence_time"] == hit_rates[0].commence_time.isoformat()
    assert summary["bettorindexpropsignals"]["side"] == "OVER"
    assert summary["bettorindexpropsignals"]["lean_label"] == "Lean Over"
    assert summary["bettorindexpropsignals"]["market_label"] == "Worth Watching"
    venue_service.build.assert_called_once()

def test_line_discrepancy_found():
    hit_rates = [
        FakeHitRate("over", 12.5, 105, "FanDuel", home_team="NYK", away_team="BKN", sport_key="nba"),
        FakeHitRate("over", 14.5, 110, "DraftKings", home_team="NYK", away_team="BKN", sport_key="nba"),
    ]
    summarizer, _ = make_summarizer_with_data(hit_rates)
    result = summarizer.find_line_discrepancy(hit_rates)
    assert result["over"]["discrepancy"] == 2.0
    assert result["over"]["min_line"] == 12.5
    assert result["over"]["max_line"] == 14.5

def test_no_line_discrepancy():
    hit_rates = [
        FakeHitRate("over", 12.5, 105, "FanDuel", home_team="NYK", away_team="BKN", sport_key="nba"),
        FakeHitRate("over", 12.5, 110, "DraftKings", home_team="NYK", away_team="BKN", sport_key="nba"),
    ]
    summarizer, _ = make_summarizer_with_data(hit_rates)
    result = summarizer.find_line_discrepancy(hit_rates)
    assert result["over"] == "No line discrepancy"

def test_best_under_line():
    hit_rates = [
        FakeHitRate("under", 13.5, 100, "FanDuel", home_team="NYK", away_team="BKN", sport_key="nba"),
        FakeHitRate("under", 14.5, 105, "DraftKings", home_team="NYK", away_team="BKN", sport_key="nba"),
    ]
    summarizer, _ = make_summarizer_with_data(hit_rates)
    best = summarizer.identify_best_under_line(hit_rates)
    assert best["outcome_line"] == 14.5
    assert best["bookmaker"] == "DraftKings"

def test_best_over_line():
    hit_rates = [
        FakeHitRate("over", 12.5, 100, "FanDuel", home_team="NYK", away_team="BKN", sport_key="nba"),
        FakeHitRate("over", 11.5, 105, "DraftKings", home_team="NYK", away_team="BKN", sport_key="nba"),
    ]
    summarizer, _ = make_summarizer_with_data(hit_rates)
    best = summarizer.identify_best_over_line(hit_rates)
    assert best["outcome_line"] == 11.5
    assert best["bookmaker"] == "DraftKings"

def test_best_under_price():
    hit_rates = [
        FakeHitRate("under", 13.5, 100, "FanDuel", home_team="NYK", away_team="BKN", sport_key="nba"),
        FakeHitRate("under", 13.5, 110, "DraftKings", home_team="NYK", away_team="BKN", sport_key="nba"),
    ]
    summarizer, _ = make_summarizer_with_data(hit_rates)
    best = summarizer.identify_best_under_price(hit_rates)
    assert best["outcome_price"] == 110
    assert best["bookmaker"] == "DraftKings"

def test_best_over_price():
    hit_rates = [
        FakeHitRate("over", 12.5, 100, "FanDuel", home_team="NYK", away_team="BKN", sport_key="nba"),
        FakeHitRate("over", 12.5, 120, "DraftKings", home_team="NYK", away_team="BKN", sport_key="nba"),
    ]
    summarizer, _ = make_summarizer_with_data(hit_rates)
    best = summarizer.identify_best_over_price(hit_rates)
    assert best["outcome_price"] == 120
    assert best["bookmaker"] == "DraftKings"

def test_odds_discrepancy_found():
    hit_rates = [
        FakeHitRate("over", 12.5, 100, "FanDuel", home_team="NYK", away_team="BKN", sport_key="nba"),
        FakeHitRate("over", 12.5, 120, "DraftKings", home_team="NYK", away_team="BKN", sport_key="nba"),
    ]
    summarizer, _ = make_summarizer_with_data(hit_rates)
    result = summarizer.find_odds_discrepancy(hit_rates)
    assert result["over"]["discrepancy"] == 20
    assert result["over"]["min_price"] == 100
    assert result["over"]["max_price"] == 120


def test_build_summary_serializes_venue_last_five_clears():
    hit_rates = [
        FakeHitRate("over", 12.5, 105, "FanDuel", home_team="NYK", away_team="BKN", sport_key="basketball_nba"),
        FakeHitRate("under", 14.5, -102, "DraftKings", home_team="NYK", away_team="BKN", sport_key="basketball_nba"),
    ]
    summarizer, venue_service = make_summarizer_with_data(hit_rates)
    venue_service.build.return_value = VenueLastFiveClears(
        venue="home",
        sample_size=2,
        window_size=5,
        over=VenueLastFiveClearsSide(line=12.5, cleared_count=2),
        under=VenueLastFiveClearsSide(line=14.5, cleared_count=1),
    )

    summary = summarizer.build_summary(hit_rates, 1, "player_points", "Over/Under")

    assert summary["venue_last_five_clears"] == {
        "venue": "home",
        "sample_size": 2,
        "window_size": 5,
        "over": {"line": 12.5, "cleared_count": 2},
        "under": {"line": 14.5, "cleared_count": 1},
    }
    request = venue_service.build.call_args.args[0]
    assert request.sport_key == "basketball_nba"
    assert request.market_key == "player_points"
    assert request.selected_over_line == 12.5
    assert request.selected_under_line == 14.5


def test_build_summary_computes_venue_last_five_clears_with_real_service():
    hit_rates = [
        FakeHitRate("over", 12.5, 105, "FanDuel", sport_key="basketball_nba", player_id=23, player_team_id=14, home_team_id=14, away_team_id=2),
        FakeHitRate("under", 14.5, -102, "DraftKings", sport_key="basketball_nba", player_id=23, player_team_id=14, home_team_id=14, away_team_id=2),
    ]
    repo = MagicMock()
    repo.get_hit_rates_by_keys.return_value = hit_rates
    signal_service = MagicMock()
    signal_service.build_signal.return_value = {}
    player_stats_repository = MagicMock()
    player_stats_repository.get_recent_player_stats.return_value = [
        {"game_id": 14, "team_id": 14, "points": 30},
        {"game_id": 13, "team_id": 14, "points": 18},
        {"game_id": 12, "team_id": 14, "points": 27},
        {"game_id": 11, "team_id": 14, "points": 21},
    ]
    game_repository = MagicMock()
    game_repository.get_games_by_ids.return_value = {
        14: SimpleNamespace(home_team_id=14, away_team_id=2),
        13: SimpleNamespace(home_team_id=2, away_team_id=14),
        12: SimpleNamespace(home_team_id=14, away_team_id=6),
        11: SimpleNamespace(home_team_id=14, away_team_id=8),
    }
    venue_service = NBAVenueLastFiveClearsService(player_stats_repository, game_repository)
    summarizer = NBASummarizer(repo, signal_service, venue_service)

    summary = summarizer.build_summary(hit_rates, 1, "player_points", "Over/Under")

    assert summary["venue_last_five_clears"] == {
        "venue": "home",
        "sample_size": 3,
        "window_size": 5,
        "over": {"line": 12.5, "cleared_count": 3},
        "under": {"line": 14.5, "cleared_count": 0},
    }
    player_stats_repository.get_recent_player_stats.assert_called_once_with(23, 50)
    game_repository.get_games_by_ids.assert_called_once_with([14, 13, 12, 11], "basketball_nba")

def test_no_odds_discrepancy():
    hit_rates = [
        FakeHitRate("over", 12.5, 100, "FanDuel", home_team="NYK", away_team="BKN", sport_key="nba"),
        FakeHitRate("over", 12.5, 100, "DraftKings", home_team="NYK", away_team="BKN", sport_key="nba"),
    ]
    summarizer, _ = make_summarizer_with_data(hit_rates)
    result = summarizer.find_odds_discrepancy(hit_rates)
    assert result["over"] == "No odds discrepancy"
