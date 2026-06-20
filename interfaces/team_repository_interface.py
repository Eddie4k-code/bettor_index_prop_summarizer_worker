from abc import ABC, abstractmethod
from typing import Optional

from db.models.teams import Team


class TeamRepositoryInterface(ABC):
    @abstractmethod
    def get_team_by_id(self, team_id: int, sport_key: str) -> Optional[Team]:
        """Retrieve a single team by team id and sport key."""
        pass