from abc import ABC, abstractmethod
from typing import Any


class NBAPlayerStatsRepositoryInterface(ABC):
    @abstractmethod
    def get_player_stats(self, player_id: int) -> list[dict[str, Any]]:
        """Retrieve the statistics for a given NBA player by their id."""
        pass

    @abstractmethod
    def get_recent_player_stats(self, player_id: int, limit: int) -> list[dict[str, Any]]:
        """Retrieve the most recent statistics for a given NBA player."""
        pass