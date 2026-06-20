from abc import ABC, abstractmethod 

class NBAPlayerStatsRepositoryInterface(ABC):
    @abstractmethod
    def get_player_stats(self, player_id: int) -> dict:
        """Retrieve the statistics for a given NBA player by their id."""
        pass