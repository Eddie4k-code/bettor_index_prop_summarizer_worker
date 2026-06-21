from interfaces.home_away_last_n_clears import HomeAwayLastNClearsInterface, HomeAwayLastNClearsResult, Under, Over
from interfaces.game_repository_interface import GameRepositoryInterface
from interfaces.mlb_player_stats_repository_interface import MLBPlayerStatsRepositoryInterface
from typing import Literal, Optional
from db.models.mlb_player_stats import MLBPlayerStats

import logging

logger = logging.getLogger(__name__)

SUPPORTED_MARKETS_MAPPING_TO_STAT = {
    'batter_home_runs': 'hr',
    'batter_hits': 'hits',
    'batter_total_bases': 'total_bases',
    'batter_rbis': 'rbi',
    'batter_singles': 'singles',
    'batter_doubles': 'doubles',
    'batter_triples': 'triples',
    'batter_walks': 'bb',
    'batter_strikeouts': 'k',
    'batter_stolen_bases': 'stolen_bases',
    'pitcher_strikeouts': 'p_k',
    'pitcher_walks': 'p_bb',
    'pitcher_earned_runs': 'er',
    'pitcher_outs': 'ip',
}

class MLBHomeAwayLastNClearsService(HomeAwayLastNClearsInterface):
    def __init__(self, player_stats_repository: MLBPlayerStatsRepositoryInterface, game_repository: GameRepositoryInterface):
        self.player_stats_repository = player_stats_repository
        self.game_repository = game_repository

    def get_last_n_clears(self, player_id: int, home_team_id: int, away_team_id: int, player_team_id: int, window: int, line: float, market: str) -> HomeAwayLastNClearsResult:

        logger.info("Calculating home/away last N clears for player_id=%s, home_team_id=%s, away_team_id=%s, player_team_id=%s, window=%s", player_id, home_team_id, away_team_id, player_team_id, window)

        game_stats = self.player_stats_repository.get_recent_player_stats(player_id, 25)

        #TODO At some point we need to check if a pitcher got a chance to pitch, and if a batter got a chance to bat to mark them as valid games.
        valid_games = [] 

        # We need to fetch all Player Game Stats for the player where they have played home.
        home_game_stats = []
        away_game_stats = []


        for stat in game_stats:
            game_id = stat.game_id
            game = self.game_repository.get_game_by_id(game_id, sport_key="baseball_mlb")

            if game is None:
                continue

            home_team_id = game.home_team_id
            away_team_id = game.away_team_id

            if home_team_id == player_team_id:
                home_game_stats.append(stat)
            elif away_team_id == player_team_id:
                away_game_stats.append(stat)
            else:
                continue

        logger.info("Found %s home game stats and %s away game stats for player_id=%s", len(home_game_stats), len(away_game_stats), player_id)

        # We then need to determine the venue for each of the games, and filter down to just the games at the requested venue (home or away).
        if len(home_game_stats) == 0 and len(away_game_stats) == 0:
            logger.warning("No game stats found for player_id=%s", player_id)
            return HomeAwayLastNClearsResult(
                home={"over": None, "under": None},
                away={"over": None, "under": None},
            )
        
        # We then need to check that there is enough games for the given window size, and if not we use the highest sample size we can find below the passed window.
        
        if len(home_game_stats) < window:
            home_window = len(home_game_stats)
        else:
            home_window = window

        if len(away_game_stats) < window:
            away_window = len(away_game_stats)
        else:
            away_window = window

        home_clears = self.calculate_home(home_window, line, market, home_game_stats)

        away_clears = self.calculate_away(away_window, line, market, away_game_stats)


        return HomeAwayLastNClearsResult(
            home=home_clears,
            away=away_clears,
        )

    def calculate_home(self, window: int, line: float, market: str, stats: list[MLBPlayerStats]) -> dict[str, Optional[Over | Under]]:
        stat = SUPPORTED_MARKETS_MAPPING_TO_STAT.get(market)
        if stat is None:
            logger.error("Unsupported market: %s", market)
            return {"over": None, "under": None}

        over_count = 0

        under_count = 0

        logger.info("Calculating home clears for stat: %s, line: %s, window: %s", stat, line, window)

        for stat_row in stats[:window]:
            stat_value = getattr(stat_row, stat, None)
            if stat_value is None:
                continue

            if stat_value > line:
                over_count += 1
            else:
                under_count += 1

        return {
            "over": Over(line=line, sample_window=window, cleared_count=over_count),
            "under": Under(line=line, sample_window=window, cleared_count=under_count),
        }

    
    def calculate_away(self, window: int, line: float, market: str, stats: list[MLBPlayerStats]) -> dict[str, Optional[Over | Under]]:
        stat = SUPPORTED_MARKETS_MAPPING_TO_STAT.get(market)
        if stat is None:
            logger.error("Unsupported market: %s", market)
            return {"over": None, "under": None}

        over_count = 0
        under_count = 0

        logger.info("Calculating away clears for stat: %s, line: %s, window: %s", stat, line, window)

        for stat_row in stats[:window]:
            stat_value = getattr(stat_row, stat, None)
            if stat_value is None:
                continue

            if stat_value > line:
                over_count += 1
            else:
                under_count += 1

        return {
            "over": Over(line=line, sample_window=window, cleared_count=over_count),
            "under": Under(line=line, sample_window=window, cleared_count=under_count),
        }
