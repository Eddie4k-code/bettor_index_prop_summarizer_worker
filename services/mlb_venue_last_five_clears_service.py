from __future__ import annotations

import logging
from typing import Any

from interfaces.game_repository_interface import GameRepositoryInterface
from interfaces.mlb_player_stats_repository_interface import MLBPlayerStatsRepositoryInterface
from interfaces.venue_last_five_clears_interface import IVenueLastFiveClearsService, VenueLastFiveClears, VenueLastFiveClearsRequest
from services.venue_last_five_clears_common import calculate_venue_last_five_clears


logger = logging.getLogger(__name__)


class MLBVenueLastFiveClearsService(IVenueLastFiveClearsService):
    DEFAULT_SUPPORTED_MARKETS: dict[str, str] = {
        "player_hits": "hits",
        "batter_hits": "hits",
        "batter_total_bases": "total_bases",
        "batter_home_runs": "hr",
        "pitcher_strikeouts": "p_k",
    }

    def __init__(
        self,
        player_stats_repository: MLBPlayerStatsRepositoryInterface,
        game_repository: GameRepositoryInterface,
        supported_markets: dict[str, str] | None = None,
        history_limit: int = 50,
        window_size: int = 5,
    ):
        self.player_stats_repository = player_stats_repository
        self.game_repository = game_repository
        self.supported_markets = supported_markets or self.DEFAULT_SUPPORTED_MARKETS
        self.history_limit = history_limit
        self.window_size = window_size

    def build(self, request: VenueLastFiveClearsRequest) -> VenueLastFiveClears | None:
        stat_field = self.supported_markets.get(request.market_key)
        if request.player_id is None or stat_field is None:
            return None

        try:
            player_stats = self.player_stats_repository.get_recent_player_stats(request.player_id, self.history_limit)
            game_ids = [row["game_id"] for row in player_stats if row.get("game_id") is not None]
            games_by_id = self.game_repository.get_games_by_ids(game_ids, request.sport_key)
        except Exception:
            logger.exception("Failed to build MLB venue last five clears for player_id=%s", request.player_id)
            return None

        return calculate_venue_last_five_clears(
            request=request,
            player_stats=player_stats,
            games_by_id=games_by_id,
            stat_getter=lambda row: row.get(stat_field),
            historical_venue_getter=self._get_historical_venue,
            window_size=self.window_size,
        )

    @staticmethod
    def _get_historical_venue(stat_row: dict[str, Any], game: Any) -> str | None:
        team_name = stat_row.get("team_name")
        if team_name is None:
            return None
        if team_name == getattr(game, "home_team", None):
            return "home"
        if team_name == getattr(game, "away_team", None):
            return "away"
        return None