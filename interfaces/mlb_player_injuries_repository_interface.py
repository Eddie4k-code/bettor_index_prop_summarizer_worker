from abc import ABC, abstractmethod

from db.models.mlb_player_injuries import MLBPlayerInjuries


class IMLBPlayerInjuriesRepository(ABC):
    @abstractmethod
    def get_injuries_for_team(self, team_id: int) -> list[MLBPlayerInjuries]:
        """Return all MLB player injuries recorded for a team."""

    @abstractmethod
    def get_injuries_for_player(self, player_id: int) -> list[MLBPlayerInjuries]:
        """Return all MLB player injuries recorded for a player."""