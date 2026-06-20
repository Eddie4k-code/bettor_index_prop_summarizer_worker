from abc import ABC, abstractmethod


class MLBPlayerStatsRepositoryInterface(ABC):
    @abstractmethod
    def get_player_stats(self, player_id: int) -> dict:
        """Retrieve the statistics for a given MLB player by their id."""
        pass