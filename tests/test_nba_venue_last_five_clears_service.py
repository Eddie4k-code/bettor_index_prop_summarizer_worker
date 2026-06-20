from types import SimpleNamespace
from unittest.mock import MagicMock

from interfaces.venue_last_five_clears_interface import VenueLastFiveClearsRequest
from services.nba_venue_last_five_clears_service import NBAVenueLastFiveClearsService


def make_service(player_stats, games_by_id):
    player_stats_repository = MagicMock()
    player_stats_repository.get_recent_player_stats.return_value = player_stats
    game_repository = MagicMock()
    game_repository.get_games_by_ids.return_value = games_by_id
    return NBAVenueLastFiveClearsService(player_stats_repository, game_repository), player_stats_repository, game_repository


def test_build_returns_partial_history_counts_for_supported_market():
    player_stats = [
        {"game_id": 14, "team_id": 14, "points": 30},
        {"game_id": 13, "team_id": 14, "points": 18},
        {"game_id": 12, "team_id": 14, "points": 27},
        {"game_id": 11, "team_id": 14, "points": 21},
    ]
    games_by_id = {
        14: SimpleNamespace(home_team_id=14, away_team_id=2),
        13: SimpleNamespace(home_team_id=2, away_team_id=14),
        12: SimpleNamespace(home_team_id=14, away_team_id=6),
        11: SimpleNamespace(home_team_id=14, away_team_id=8),
    }
    service, player_stats_repository, game_repository = make_service(player_stats, games_by_id)
    request = VenueLastFiveClearsRequest(
        sport_key="basketball_nba",
        player_id=23,
        market_key="player_points",
        outcome_description="LeBron James",
        selected_over_line=22.5,
        selected_under_line=25.5,
        player_team_id=14,
        home_team_id=14,
        away_team_id=2,
    )

    result = service.build(request)

    assert result is not None
    assert result.venue == "home"
    assert result.sample_size == 3
    assert result.window_size == 5
    assert result.over.cleared_count == 2
    assert result.under.cleared_count == 1
    player_stats_repository.get_recent_player_stats.assert_called_once_with(23, 50)
    game_repository.get_games_by_ids.assert_called_once_with([14, 13, 12, 11], "basketball_nba")


def test_build_uses_larger_history_buffer_but_only_counts_five_matching_venue_games():
    player_stats = [
        {"game_id": 20, "team_id": 14, "points": 29},
        {"game_id": 19, "team_id": 14, "points": 10},
        {"game_id": 18, "team_id": 14, "points": 26},
        {"game_id": 17, "team_id": 14, "points": 24},
        {"game_id": 16, "team_id": 14, "points": 18},
        {"game_id": 15, "team_id": 14, "points": 31},
        {"game_id": 14, "team_id": 14, "points": 33},
    ]
    games_by_id = {
        20: SimpleNamespace(home_team_id=14, away_team_id=2),
        19: SimpleNamespace(home_team_id=5, away_team_id=14),
        18: SimpleNamespace(home_team_id=14, away_team_id=6),
        17: SimpleNamespace(home_team_id=14, away_team_id=8),
        16: SimpleNamespace(home_team_id=3, away_team_id=14),
        15: SimpleNamespace(home_team_id=14, away_team_id=9),
        14: SimpleNamespace(home_team_id=14, away_team_id=2),
    }
    service, player_stats_repository, _ = make_service(player_stats, games_by_id)
    request = VenueLastFiveClearsRequest(
        sport_key="basketball_nba",
        player_id=23,
        market_key="player_points",
        outcome_description="LeBron James",
        selected_over_line=22.5,
        selected_under_line=30.5,
        player_team_id=14,
        home_team_id=14,
        away_team_id=2,
    )

    result = service.build(request)

    assert result is not None
    assert result.venue == "home"
    assert result.sample_size == 5
    assert result.over.cleared_count == 5
    assert result.under.cleared_count == 3
    player_stats_repository.get_recent_player_stats.assert_called_once_with(23, 50)


def test_build_returns_zero_sample_object_when_no_matching_venue_history():
    player_stats = [
        {"game_id": 14, "team_id": 14, "points": 30},
        {"game_id": 12, "team_id": 14, "points": 27},
    ]
    games_by_id = {
        14: SimpleNamespace(home_team_id=14, away_team_id=2),
        12: SimpleNamespace(home_team_id=14, away_team_id=6),
    }
    service, _, _ = make_service(player_stats, games_by_id)
    request = VenueLastFiveClearsRequest(
        sport_key="basketball_nba",
        player_id=23,
        market_key="player_points",
        outcome_description="LeBron James",
        selected_over_line=22.5,
        selected_under_line=25.5,
        player_team_id=2,
        home_team_id=14,
        away_team_id=2,
    )

    result = service.build(request)

    assert result is not None
    assert result.venue == "away"
    assert result.sample_size == 0
    assert result.over.cleared_count == 0
    assert result.under.cleared_count == 0


def test_build_returns_none_for_missing_current_venue_context():
    service, _, _ = make_service([], {})
    request = VenueLastFiveClearsRequest(
        sport_key="basketball_nba",
        player_id=23,
        market_key="player_points",
        outcome_description="LeBron James",
        selected_over_line=22.5,
        selected_under_line=25.5,
        player_team_id=None,
        home_team_id=14,
        away_team_id=2,
    )

    assert service.build(request) is None