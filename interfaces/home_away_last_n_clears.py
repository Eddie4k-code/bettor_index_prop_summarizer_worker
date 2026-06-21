from abc import ABC, abstractmethod
from typing import Optional, Literal
from pydantic import BaseModel

class Over(BaseModel):
    line: float
    sample_window: int
    cleared_count: int

class Under(BaseModel):
    line: float
    sample_window: int
    cleared_count: int

class HomeAwayLastNClearsResult(BaseModel):
    away: dict[str, Optional[Over | Under]]
    home: dict[str, Optional[Over | Under]]

    def to_dict(self) -> dict:
        return {
            "home": {
                "over": self._serialize_side(self.home.get("over")),
                "under": self._serialize_side(self.home.get("under")),
            },
            "away": {
                "over": self._serialize_side(self.away.get("over")),
                "under": self._serialize_side(self.away.get("under")),
            },
        }

    @staticmethod
    def _serialize_side(side: Over | Under | None) -> dict | None:
        if side is None:
            return None

        return {
            "line": side.line,
            "sample_window": side.sample_window,
            "cleared_count": side.cleared_count,
        }

class HomeAwayLastNClearsInterface(ABC):
    @abstractmethod
    def get_last_n_clears(self, player_id: int, home_team_id: int, away_team_id: int, player_team_id: int, window: int, line: float, market: str) -> Optional[HomeAwayLastNClearsResult]:
        """Retrieve the number of clears for the last N games for a given player at a specific venue (home/away)."""
        pass



