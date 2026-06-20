from abc import ABC, abstractmethod
from typing import Optional

from db.models.games import Game


class GameRepositoryInterface(ABC):
    @abstractmethod
    def get_game_by_id(self, game_id: int, sport_key: str) -> Optional[Game]:
        """Retrieve a single game by game id and sport key."""
        pass