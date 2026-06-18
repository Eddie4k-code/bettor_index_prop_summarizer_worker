from collections.abc import Callable
from datetime import datetime, timedelta

from db.models.mlb_player_injuries import MLBPlayerInjuries
from interfaces.mlb_player_injuries_repository_interface import IMLBPlayerInjuriesRepository
from interfaces.relevant_injury_context_interface import (
    PropInjuryContext,
    RelevantInjuryContext,
    RelevantInjuryContextInterface,
)


HITTER_MARKETS = {
    "batter_home_runs",
    "batter_hits",
    "batter_total_bases",
    "batter_rbis",
    "batter_runs_scored",
    "batter_hits_runs_rbis",
    "batter_singles",
    "batter_doubles",
    "batter_triples",
    "batter_walks",
    "batter_strikeouts",
    "batter_stolen_bases",
    "batter_fantasy_score",
}

PITCHER_MARKETS = {
    "pitcher_strikeouts",
    "pitcher_hits_allowed",
    "pitcher_walks",
    "pitcher_earned_runs",
    "pitcher_outs",
}

PITCHER_POSITIONS = {
    "SP",
    "RP",
    "Starting Pitcher",
    "Relief Pitcher",
}

HITTER_POSITIONS = {
    "1B",
    "2B",
    "3B",
    "C",
    "CF",
    "Catcher",
    "Center Fielder",
    "DH",
    "Designated Hitter",
    "First Baseman",
    "LF",
    "Left Fielder",
    "RF",
    "Right Fielder",
    "SS",
    "Second Baseman",
    "Shortstop",
    "Third Baseman",
}


class MLBRelevantInjuryContextService(RelevantInjuryContextInterface):
    def __init__(
        self,
        mlb_player_injuries_repository: IMLBPlayerInjuriesRepository,
        recency_days: int = 14,
        active_statuses: set[str] | None = None,
        now_provider: Callable[[], datetime] | None = None,
    ):
        self.mlb_player_injuries_repository = mlb_player_injuries_repository
        self.recency_days = recency_days
        self.active_statuses = {status.lower() for status in (active_statuses or {"out", "day-to-day"})}
        self.now_provider = now_provider or datetime.utcnow

    def get_relevant_injury_context(self, prop_context: PropInjuryContext) -> list[RelevantInjuryContext]:
        market_group = self._classify_market(prop_context.market_key)
        if market_group is None:
            return []

        relevant_injuries: list[RelevantInjuryContext] = []
        if prop_context.player_id is not None:
            player_injuries = self.mlb_player_injuries_repository.get_injuries_for_player(prop_context.player_id)
            relevant_injuries.extend(self._build_direct_player_matches(player_injuries, market_group, prop_context))

        opposing_team_id = self._get_opposing_team_id(prop_context)
        if opposing_team_id is None:
            return relevant_injuries

        opposing_team_injuries = self.mlb_player_injuries_repository.get_injuries_for_team(opposing_team_id)
        if market_group == "hitter":
            relevant_injuries.extend(
                self._build_opposing_team_matches(
                    injuries=opposing_team_injuries,
                    expected_role="pitcher",
                    reason_template="Opposing pitcher injury may affect this batter prop",
                    relevance_type="opposing_pitcher_injury",
                    market_key=prop_context.market_key,
                )
            )
        elif market_group == "pitcher":
            relevant_injuries.extend(
                self._build_opposing_team_matches(
                    injuries=opposing_team_injuries,
                    expected_role="hitter",
                    reason_template="Opposing lineup weakness may affect this pitcher prop",
                    relevance_type="opposing_lineup_weakness",
                    market_key=prop_context.market_key,
                )
            )

        return relevant_injuries

    def _build_direct_player_matches(
        self,
        injuries: list[MLBPlayerInjuries],
        market_group: str,
        prop_context: PropInjuryContext,
    ) -> list[RelevantInjuryContext]:
        expected_role = "hitter" if market_group == "hitter" else "pitcher"
        relevance_type = "direct_player_injury"
        reason = f"Prop player has a relevant {expected_role} injury for this market"

        return [
            self._to_relevant_injury_context(
                injury,
                relevance_reason=reason,
                metadata={
                    "market_group": market_group,
                    "market_key": prop_context.market_key,
                    "normalized_role": expected_role,
                    "relevance_type": relevance_type,
                },
            )
            for injury in injuries
            if self._is_relevant_injury(injury, expected_role)
        ]

    def _build_opposing_team_matches(
        self,
        injuries: list[MLBPlayerInjuries],
        expected_role: str,
        reason_template: str,
        relevance_type: str,
        market_key: str,
    ) -> list[RelevantInjuryContext]:
        return [
            self._to_relevant_injury_context(
                injury,
                relevance_reason=reason_template,
                metadata={
                    "market_group": "hitter" if expected_role == "pitcher" else "pitcher",
                    "market_key": market_key,
                    "normalized_role": expected_role,
                    "relevance_type": relevance_type,
                },
            )
            for injury in injuries
            if self._is_relevant_injury(injury, expected_role)
        ]

    def _is_relevant_injury(self, injury: MLBPlayerInjuries, expected_role: str) -> bool:
        if self._normalize_position(injury.position) != expected_role:
            return False

        status = (injury.status or "").strip().lower()
        if status not in self.active_statuses:
            return False

        if injury.return_date is not None and injury.return_date >= self.now_provider():
            return True

        if injury.date is None:
            return True

        return injury.date >= self.now_provider() - timedelta(days=self.recency_days)

    def _get_opposing_team_id(self, prop_context: PropInjuryContext) -> int | None:
        if prop_context.player_team_id is None:
            return None

        if prop_context.player_team_id == prop_context.home_team_id:
            return prop_context.away_team_id

        if prop_context.player_team_id == prop_context.away_team_id:
            return prop_context.home_team_id

        return None

    def _classify_market(self, market_key: str) -> str | None:
        if market_key in HITTER_MARKETS:
            return "hitter"
        if market_key in PITCHER_MARKETS:
            return "pitcher"
        return None

    def _normalize_position(self, position: str | None) -> str:
        if position in PITCHER_POSITIONS:
            return "pitcher"
        if position in HITTER_POSITIONS:
            return "hitter"
        return "unknown"

    def _to_relevant_injury_context(
        self,
        injury: MLBPlayerInjuries,
        relevance_reason: str,
        metadata: dict[str, str],
    ) -> RelevantInjuryContext:
        return RelevantInjuryContext(
            player_id=injury.player_id,
            team_id=injury.team_id,
            date=injury.date,
            return_date=injury.return_date,
            display_name=injury.display_name,
            position=injury.position,
            type=injury.type,
            detail=injury.detail,
            side=injury.side,
            status=injury.status,
            long_comment=injury.long_comment,
            short_comment=injury.short_comment,
            relevance_reason=relevance_reason,
            metadata=metadata,
        )