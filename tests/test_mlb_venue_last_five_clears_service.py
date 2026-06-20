from types import SimpleNamespace
from unittest.mock import MagicMock

from interfaces.venue_last_five_clears_interface import VenueLastFiveClearsRequest
from services.mlb_venue_last_five_clears_service import MLBVenueLastFiveClearsService


def make_service(player_stats, games_by_id):
    player_stats_repository = MagicMock()
    player_stats_repository.get_recent_player_stats.return_value = player_stats
    game_repository = MagicMock()
    game_repository.get_games_by_ids.return_value = games_by_id
    return MLBVenueLastFiveClearsService(player_stats_repository, game_repository), player_stats_repository, game_repository


def test_build_returns_partial_history_counts_for_supported_market():
    player_stats = [
        {"game_id": 4, "team_name": "Yankees", "hits": 3},
        {"game_id": 3, "team_name": "Yankees", "hits": 1},
        {"game_id": 2, "team_name": "Yankees", "hits": 2},
        {"game_id": 1, "team_name": "Yankees", "hits": 0},
    ]
    games_by_id = {
        4: SimpleNamespace(home_team="Yankees", away_team="Red Sox"),
        3: SimpleNamespace(home_team="Blue Jays", away_team="Yankees"),
        2: SimpleNamespace(home_team="Yankees", away_team="Orioles"),
        1: SimpleNamespace(home_team="Yankees", away_team="Rays"),
    }
    service, player_stats_repository, game_repository = make_service(player_stats, games_by_id)
    request = VenueLastFiveClearsRequest(
        sport_key="baseball_mlb",
        player_id=77,
        market_key="player_hits",
        outcome_description="Aaron Judge",
        selected_over_line=1.5,
        selected_under_line=2.5,
        player_team_id=10,
        home_team_id=10,
        away_team_id=20,
    )

    result = service.build(request)

    assert result is not None
    assert result.venue == "home"
    assert result.sample_size == 3
    assert result.window_size == 5
    assert result.over.line == 1.5
    assert result.over.cleared_count == 2
    assert result.under.line == 2.5
    assert result.under.cleared_count == 2
    player_stats_repository.get_recent_player_stats.assert_called_once_with(77, 50)
    game_repository.get_games_by_ids.assert_called_once_with([4, 3, 2, 1], "baseball_mlb")


def test_build_uses_larger_history_buffer_but_only_counts_five_matching_venue_games():
    player_stats = [
        {"game_id": 10, "team_name": "Yankees", "hits": 4},
        {"game_id": 9, "team_name": "Yankees", "hits": 1},
        {"game_id": 8, "team_name": "Yankees", "hits": 3},
        {"game_id": 7, "team_name": "Yankees", "hits": 0},
        {"game_id": 6, "team_name": "Yankees", "hits": 2},
        {"game_id": 5, "team_name": "Yankees", "hits": 5},
        {"game_id": 4, "team_name": "Yankees", "hits": 6},
    ]
    games_by_id = {
        10: SimpleNamespace(home_team="Blue Jays", away_team="Yankees"),
        9: SimpleNamespace(home_team="Yankees", away_team="Red Sox"),
        8: SimpleNamespace(home_team="Blue Jays", away_team="Yankees"),
        7: SimpleNamespace(home_team="Blue Jays", away_team="Yankees"),
        6: SimpleNamespace(home_team="Yankees", away_team="Orioles"),
        5: SimpleNamespace(home_team="Blue Jays", away_team="Yankees"),
        4: SimpleNamespace(home_team="Blue Jays", away_team="Yankees"),
    }
    service, player_stats_repository, _ = make_service(player_stats, games_by_id)
    request = VenueLastFiveClearsRequest(
        sport_key="baseball_mlb",
        player_id=77,
        market_key="player_hits",
        outcome_description="Aaron Judge",
        selected_over_line=1.5,
        selected_under_line=3.5,
        player_team_id=20,
        home_team_id=10,
        away_team_id=20,
    )

    result = service.build(request)

    assert result is not None
    assert result.venue == "away"
    assert result.sample_size == 5
    assert result.over.cleared_count == 4
    assert result.under.cleared_count == 2
    player_stats_repository.get_recent_player_stats.assert_called_once_with(77, 50)


def test_build_returns_zero_sample_object_when_no_matching_venue_history():
    player_stats = [
        {"game_id": 4, "team_name": "Yankees", "hits": 3},
        {"game_id": 3, "team_name": "Yankees", "hits": 1},
    ]
    games_by_id = {
        4: SimpleNamespace(home_team="Yankees", away_team="Red Sox"),
        3: SimpleNamespace(home_team="Yankees", away_team="Blue Jays"),
    }
    service, _, _ = make_service(player_stats, games_by_id)
    request = VenueLastFiveClearsRequest(
        sport_key="baseball_mlb",
        player_id=77,
        market_key="player_hits",
        outcome_description="Aaron Judge",
        selected_over_line=1.5,
        selected_under_line=2.5,
        player_team_id=20,
        home_team_id=10,
        away_team_id=20,
    )

    result = service.build(request)

    assert result is not None
    assert result.venue == "away"
    assert result.sample_size == 0
    assert result.over.cleared_count == 0
    assert result.under.cleared_count == 0


def test_build_returns_none_for_unsupported_market():
    service, _, _ = make_service([], {})
    request = VenueLastFiveClearsRequest(
        sport_key="baseball_mlb",
        player_id=77,
        market_key="unsupported_market",
        outcome_description="Aaron Judge",
        selected_over_line=1.5,
        selected_under_line=2.5,
        player_team_id=10,
        home_team_id=10,
        away_team_id=20,
    )

    assert service.build(request) is None