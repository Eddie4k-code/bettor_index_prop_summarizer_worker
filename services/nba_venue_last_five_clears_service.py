from __future__ import annotations

import logging

from interfaces.game_repository_interface import GameRepositoryInterface
from interfaces.nba_player_stats_repository_interface import NBAPlayerStatsRepositoryInterface
from interfaces.venue_last_five_clears_interface import IVenueLastFiveClearsService, VenueLastFiveClears, VenueLastFiveClearsRequest
from services.venue_last_five_clears_common import calculate_venue_last_five_clears


logger = logging.getLogger(__name__)


class NBAVenueLastFiveClearsService(IVenueLastFiveClearsService):
    DEFAULT_SUPPORTED_MARKETS: dict[str, str] = {
        "player_points": "points",
        "player_rebounds": "totReb",
        "player_assists": "assists",
        "player_blocks": "blocks",
        "player_steals": "steals",
        "player_threes": "tpm",
    }

    def __init__(
        self,
        player_stats_repository: NBAPlayerStatsRepositoryInterface,
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
            logger.exception("Failed to build NBA venue last five clears for player_id=%s", request.player_id)
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
    def _get_historical_venue(stat_row: dict, game) -> str | None:
        team_id = stat_row.get("team_id")
        if team_id is None:
            return None
        if team_id == getattr(game, "home_team_id", None):
            return "home"
        if team_id == getattr(game, "away_team_id", None):
            return "away"
        return None