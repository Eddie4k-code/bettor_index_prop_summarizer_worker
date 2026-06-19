from datetime import datetime
from unittest.mock import Mock

import pytest

from db.models.mlb_player_injuries import MLBPlayerInjuries
from interfaces.relevant_injury_context_interface import PropInjuryContext
from services.mlb_relevant_injury_context_service import MLBRelevantInjuryContextService


NOW = datetime(2026, 6, 17, 12, 0, 0)


def build_injury(
    *,
    player_id: int,
    team_id: int,
    position: str,
    status: str = "out",
    date: datetime | None = None,
    return_date: datetime | None = None,
    display_name: str = "Player",
):
    return MLBPlayerInjuries(
        player_id=player_id,
        team_id=team_id,
        date=date or NOW,
        return_date=return_date,
        display_name=display_name,
        position=position,
        type="hamstring",
        detail="starter",
        side="left",
        status=status,
        long_comment="long",
        short_comment="short",
    )


def make_service(player_injuries=None, team_injuries=None):
    repo = Mock()
    repo.get_injuries_for_player.return_value = player_injuries or []
    repo.get_injuries_for_team.return_value = team_injuries or []
    service = MLBRelevantInjuryContextService(repo, now_provider=lambda: NOW)
    return service, repo


def test_hitter_prop_returns_direct_hitter_and_opposing_pitcher_injuries():
    player_injury = build_injury(player_id=10, team_id=100, position="CF", display_name="Batter A")
    opposing_pitcher_injury = build_injury(player_id=99, team_id=200, position="SP", display_name="Pitcher B")
    service, repo = make_service([player_injury], [opposing_pitcher_injury])

    context = PropInjuryContext(
        sport_key="baseball_mlb",
        event_id="evt1",
        market_key="batter_hits",
        outcome_description="Batter A",
        home_team_id=100,
        away_team_id=200,
        player_id=10,
        player_team_id=100,
    )

    results = service.get_relevant_injury_context(context)

    assert len(results) == 2
    assert results[0].metadata["relevance_type"] == "direct_player_injury"
    assert results[1].metadata["relevance_type"] == "opposing_pitcher_injury"
    assert results[0].metadata["market_family"] == "batter_contact_props"
    repo.get_injuries_for_player.assert_called_once_with(10)
    repo.get_injuries_for_team.assert_called_once_with(200)


def test_pitcher_prop_returns_direct_pitcher_and_opposing_lineup_weakness():
    pitcher_injury = build_injury(player_id=40, team_id=100, position="Starting Pitcher", display_name="Pitcher A")
    opposing_hitter_injury = build_injury(player_id=50, team_id=200, position="1B", display_name="Hitter B")
    service, _ = make_service([pitcher_injury], [opposing_hitter_injury])

    context = PropInjuryContext(
        sport_key="baseball_mlb",
        event_id="evt2",
        market_key="pitcher_strikeouts",
        outcome_description="Pitcher A",
        home_team_id=100,
        away_team_id=200,
        player_id=40,
        player_team_id=100,
    )

    results = service.get_relevant_injury_context(context)

    assert len(results) == 2
    assert results[0].metadata["relevance_type"] == "direct_player_injury"
    assert results[1].metadata["relevance_type"] == "opposing_lineup_weakness"


def test_batter_runs_scored_includes_same_team_lineup_weakness():
    player_injury = build_injury(player_id=10, team_id=100, position="CF", display_name="Batter A")
    opposing_pitcher_injury = build_injury(player_id=99, team_id=200, position="SP", display_name="Pitcher B")
    same_team_hitter_injury = build_injury(player_id=11, team_id=100, position="1B", display_name="Teammate C")

    repo = Mock()
    repo.get_injuries_for_player.return_value = [player_injury]
    repo.get_injuries_for_team.side_effect = [[opposing_pitcher_injury], [same_team_hitter_injury]]
    service = MLBRelevantInjuryContextService(repo, now_provider=lambda: NOW)

    context = PropInjuryContext(
        sport_key="baseball_mlb",
        event_id="evt6",
        market_key="batter_runs_scored",
        outcome_description="Batter A",
        home_team_id=100,
        away_team_id=200,
        player_id=10,
        player_team_id=100,
    )

    results = service.get_relevant_injury_context(context)

    assert len(results) == 3
    assert results[1].metadata["relevance_type"] == "opposing_pitcher_injury"
    assert results[2].metadata["relevance_type"] == "same_team_lineup_weakness"
    assert results[2].metadata["context_side"] == "same"


def test_batter_total_bases_excludes_same_team_lineup_weakness():
    player_injury = build_injury(player_id=10, team_id=100, position="CF", display_name="Batter A")
    opposing_pitcher_injury = build_injury(player_id=99, team_id=200, position="SP", display_name="Pitcher B")
    service, repo = make_service([player_injury], [opposing_pitcher_injury])

    context = PropInjuryContext(
        sport_key="baseball_mlb",
        event_id="evt7",
        market_key="batter_total_bases",
        outcome_description="Batter A",
        home_team_id=100,
        away_team_id=200,
        player_id=10,
        player_team_id=100,
    )

    results = service.get_relevant_injury_context(context)

    assert len(results) == 2
    assert all(result.metadata["relevance_type"] != "same_team_lineup_weakness" for result in results)
    repo.get_injuries_for_team.assert_called_once_with(200)


def test_batter_home_runs_excludes_same_team_lineup_weakness():
    player_injury = build_injury(player_id=10, team_id=100, position="1B", display_name="Batter A")
    opposing_pitcher_injury = build_injury(player_id=99, team_id=200, position="SP", display_name="Pitcher B")
    service, _ = make_service([player_injury], [opposing_pitcher_injury])

    context = PropInjuryContext(
        sport_key="baseball_mlb",
        event_id="evt8",
        market_key="batter_home_runs",
        outcome_description="Batter A",
        home_team_id=100,
        away_team_id=200,
        player_id=10,
        player_team_id=100,
    )

    results = service.get_relevant_injury_context(context)

    assert len(results) == 2
    assert all(result.metadata["context_side"] != "same" for result in results)


def test_stale_injuries_are_excluded_without_future_return_date():
    stale_injury = build_injury(
        player_id=10,
        team_id=100,
        position="CF",
        date=datetime(2026, 5, 1, 12, 0, 0),
        return_date=None,
    )
    service, _ = make_service([stale_injury], [])

    context = PropInjuryContext(
        sport_key="baseball_mlb",
        event_id="evt3",
        market_key="batter_hits",
        outcome_description="Batter A",
        player_id=10,
        player_team_id=100,
        home_team_id=100,
        away_team_id=200,
    )

    results = service.get_relevant_injury_context(context)

    assert results == []


def test_future_return_date_keeps_recent_status_relevant():
    injury = build_injury(
        player_id=10,
        team_id=100,
        position="CF",
        date=datetime(2026, 5, 1, 12, 0, 0),
        return_date=datetime(2026, 6, 20, 12, 0, 0),
    )
    service, _ = make_service([injury], [])

    context = PropInjuryContext(
        sport_key="baseball_mlb",
        event_id="evt4",
        market_key="batter_hits",
        outcome_description="Batter A",
        player_id=10,
        player_team_id=100,
        home_team_id=100,
        away_team_id=200,
    )

    results = service.get_relevant_injury_context(context)

    assert len(results) == 1


@pytest.mark.parametrize(
    "status",
    [
        "day-to-day",
        "7-day-il",
        "10-day-il",
        "15-day-il",
        "60-day-il",
        "7-Day-IL",
        "10-DAY-IL",
        "15-Day-IL",
        "60-Day-IL",
    ],
)
def test_active_mlb_statuses_are_case_insensitive(status: str):
    injury = build_injury(
        player_id=10,
        team_id=100,
        position="CF",
        status=status,
    )
    service, _ = make_service([injury], [])

    context = PropInjuryContext(
        sport_key="baseball_mlb",
        event_id="evt9",
        market_key="batter_hits",
        outcome_description="Batter A",
        player_id=10,
        player_team_id=100,
        home_team_id=100,
        away_team_id=200,
    )

    results = service.get_relevant_injury_context(context)

    assert len(results) == 1


def test_unsupported_status_is_excluded():
    injury = build_injury(
        player_id=10,
        team_id=100,
        position="CF",
        status="probable",
    )
    service, _ = make_service([injury], [])

    context = PropInjuryContext(
        sport_key="baseball_mlb",
        event_id="evt10",
        market_key="batter_hits",
        outcome_description="Batter A",
        player_id=10,
        player_team_id=100,
        home_team_id=100,
        away_team_id=200,
    )

    results = service.get_relevant_injury_context(context)

    assert results == []


def test_unsupported_market_returns_no_results():
    service, repo = make_service()

    context = PropInjuryContext(
        sport_key="baseball_mlb",
        event_id="evt5",
        market_key="pitcher_record_a_win",
        outcome_description="Pitcher A",
        player_id=40,
        player_team_id=100,
        home_team_id=100,
        away_team_id=200,
    )

    results = service.get_relevant_injury_context(context)

    assert results == []
    repo.get_injuries_for_player.assert_not_called()
    repo.get_injuries_for_team.assert_not_called()