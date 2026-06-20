from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Literal


VenueType = Literal["home", "away"]


@dataclass(frozen=True)
class VenueLastFiveClearsSide:
    line: float | None
    cleared_count: int


@dataclass(frozen=True)
class VenueLastFiveClears:
    venue: VenueType
    sample_size: int
    window_size: int
    over: VenueLastFiveClearsSide | None
    under: VenueLastFiveClearsSide | None

    def to_dict(self) -> dict:
        return {
            "venue": self.venue,
            "sample_size": self.sample_size,
            "window_size": self.window_size,
            "over": self._serialize_side(self.over),
            "under": self._serialize_side(self.under),
        }

    @staticmethod
    def _serialize_side(side: VenueLastFiveClearsSide | None) -> dict | None:
        if side is None:
            return None

        return {
            "line": side.line,
            "cleared_count": side.cleared_count,
        }


@dataclass(frozen=True)
class VenueLastFiveClearsRequest:
    sport_key: str
    player_id: int | None
    market_key: str
    outcome_description: str
    selected_over_line: float | None
    selected_under_line: float | None
    player_team_id: int | None
    home_team_id: int | None
    away_team_id: int | None


class IVenueLastFiveClearsService(ABC):
    @abstractmethod
    def build(self, request: VenueLastFiveClearsRequest) -> VenueLastFiveClears | None:
        """Build a venue-aware last-five-clears payload for a summary."""