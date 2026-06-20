from __future__ import annotations

from typing import Any, Callable

from interfaces.venue_last_five_clears_interface import (
    VenueLastFiveClears,
    VenueLastFiveClearsRequest,
    VenueLastFiveClearsSide,
)


StatValueGetter = Callable[[dict[str, Any]], int | float | None]
HistoricalVenueGetter = Callable[[dict[str, Any], Any], str | None]


def determine_requested_venue(request: VenueLastFiveClearsRequest) -> str | None:
    if request.player_team_id is None:
        return None
    if request.player_team_id == request.home_team_id:
        return "home"
    if request.player_team_id == request.away_team_id:
        return "away"
    return None


def calculate_venue_last_five_clears(
    request: VenueLastFiveClearsRequest,
    player_stats: list[dict[str, Any]],
    games_by_id: dict[int, Any],
    stat_getter: StatValueGetter | None,
    historical_venue_getter: HistoricalVenueGetter,
    window_size: int = 5,
) -> VenueLastFiveClears | None:
    requested_venue = determine_requested_venue(request)
    if requested_venue is None or stat_getter is None:
        return None

    matching_stats: list[int | float] = []
    for stat_row in player_stats:
        game_id = stat_row.get("game_id")
        game = games_by_id.get(game_id)
        if game is None:
            continue

        historical_venue = historical_venue_getter(stat_row, game)
        if historical_venue != requested_venue:
            continue

        stat_value = stat_getter(stat_row)
        if stat_value is None:
            continue

        matching_stats.append(stat_value)
        if len(matching_stats) == window_size:
            break

    return VenueLastFiveClears(
        venue=requested_venue,
        sample_size=len(matching_stats),
        window_size=window_size,
        over=_build_side(request.selected_over_line, matching_stats, is_over=True),
        under=_build_side(request.selected_under_line, matching_stats, is_over=False),
    )


def _build_side(
    line: float | None,
    matching_stats: list[int | float],
    *,
    is_over: bool,
) -> VenueLastFiveClearsSide | None:
    if line is None:
        return None

    if is_over:
        cleared_count = sum(1 for stat_value in matching_stats if stat_value > line)
    else:
        cleared_count = sum(1 for stat_value in matching_stats if stat_value < line)

    return VenueLastFiveClearsSide(line=line, cleared_count=cleared_count)