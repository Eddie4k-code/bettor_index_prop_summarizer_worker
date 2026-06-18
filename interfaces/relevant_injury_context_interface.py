from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from typing import Any


@dataclass(frozen=True)
class PropInjuryContext:
    sport_key: str
    event_id: str
    market_key: str
    outcome_description: str
    home_team_id: int | None = None
    away_team_id: int | None = None
    player_id: int | None = None
    player_team_id: int | None = None


@dataclass(frozen=True)
class RelevantInjuryContext:
    player_id: int
    team_id: int | None
    date: datetime | None
    return_date: datetime | None
    display_name: str | None
    position: str | None
    type: str | None
    detail: str | None
    side: str | None
    status: str | None
    long_comment: str | None
    short_comment: str | None
    relevance_reason: str
    metadata: dict[str, Any] | None = None


class RelevantInjuryContextInterface(ABC):
    @abstractmethod
    def get_relevant_injury_context(self, prop_context: PropInjuryContext) -> list[RelevantInjuryContext]:
        pass
