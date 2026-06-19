from collections.abc import Callable
from datetime import datetime, timedelta

from db.models.mlb_player_injuries import MLBPlayerInjuries
from interfaces.mlb_player_injuries_repository_interface import IMLBPlayerInjuriesRepository
from interfaces.relevant_injury_context_interface import (
    PropInjuryContext,
    RelevantInjuryContext,
    RelevantInjuryContextInterface,
)

MARKET_FAMILIES = {
    "pitcher_strikeouts": "pitcher_props",
    "pitcher_hits_allowed": "pitcher_props",
    "pitcher_walks": "pitcher_props",
    "pitcher_earned_runs": "pitcher_props",
    "pitcher_outs": "pitcher_props",
    "batter_hits": "batter_contact_props",
    "batter_singles": "batter_contact_props",
    "batter_doubles": "batter_contact_props",
    "batter_triples": "batter_contact_props",
    "batter_home_runs": "batter_power_props",
    "batter_rbis": "batter_power_props",
    "batter_total_bases": "batter_total_base_props",
    "batter_hits_runs_rbis": "batter_total_base_props",
    "batter_runs_scored": "batter_scoring_props",
    "batter_stolen_bases": "batter_speed_props",
    "batter_walks": "batter_plate_discipline_props",
    "batter_strikeouts": "batter_plate_discipline_props",
    "batter_fantasy_score": "batter_fantasy_props",
}

DIRECT_PLAYER_ROLE_BY_FAMILY = {
    "pitcher_props": "pitcher",
    "batter_contact_props": "hitter",
    "batter_power_props": "hitter",
    "batter_total_base_props": "hitter",
    "batter_scoring_props": "hitter",
    "batter_speed_props": "hitter",
    "batter_plate_discipline_props": "hitter",
    "batter_fantasy_props": "hitter",
}

TEAM_CONTEXTS_BY_FAMILY = {
    "pitcher_props": [
        {
            "team_side": "opposing",
            "expected_role": "hitter",
            "reason_template": "Opposing lineup weakness may affect this pitcher prop",
            "relevance_type": "opposing_lineup_weakness",
        }
    ],
    "batter_contact_props": [
        {
            "team_side": "opposing",
            "expected_role": "pitcher",
            "reason_template": "Opposing pitcher injury may affect this batter prop",
            "relevance_type": "opposing_pitcher_injury",
        }
    ],
    "batter_power_props": [
        {
            "team_side": "opposing",
            "expected_role": "pitcher",
            "reason_template": "Opposing pitcher injury may affect this batter prop",
            "relevance_type": "opposing_pitcher_injury",
        }
    ],
    "batter_total_base_props": [
        {
            "team_side": "opposing",
            "expected_role": "pitcher",
            "reason_template": "Opposing pitcher injury may affect this batter prop",
            "relevance_type": "opposing_pitcher_injury",
        }
    ],
    "batter_scoring_props": [
        {
            "team_side": "opposing",
            "expected_role": "pitcher",
            "reason_template": "Opposing pitcher injury may affect this batter prop",
            "relevance_type": "opposing_pitcher_injury",
        },
        {
            "team_side": "same",
            "expected_role": "hitter",
            "reason_template": "Same-team lineup injuries may reduce run-scoring support for this batter prop",
            "relevance_type": "same_team_lineup_weakness",
        },
    ],
    "batter_speed_props": [],
    "batter_plate_discipline_props": [
        {
            "team_side": "opposing",
            "expected_role": "pitcher",
            "reason_template": "Opposing pitcher injury may affect this batter prop",
            "relevance_type": "opposing_pitcher_injury",
        }
    ],
    "batter_fantasy_props": [
        {
            "team_side": "opposing",
            "expected_role": "pitcher",
            "reason_template": "Opposing pitcher injury may affect this batter prop",
            "relevance_type": "opposing_pitcher_injury",
        }
    ],
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

DEFAULT_ACTIVE_STATUSES = {
    "out",
    "day-to-day",
    "7-day-il",
    "10-day-il",
    "15-day-il",
    "60-day-il",
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
        self.active_statuses = {status.lower() for status in (active_statuses or DEFAULT_ACTIVE_STATUSES)}
        self.now_provider = now_provider or datetime.utcnow

    def get_relevant_injury_context(self, prop_context: PropInjuryContext) -> list[RelevantInjuryContext]:
        market_family = self._classify_market_family(prop_context.market_key)
        if market_family is None:
            return []

        relevant_injuries: list[RelevantInjuryContext] = []
        if prop_context.player_id is not None:
            player_injuries = self.mlb_player_injuries_repository.get_injuries_for_player(prop_context.player_id)
            relevant_injuries.extend(self._build_direct_player_matches(player_injuries, market_family, prop_context))

        for context_rule in TEAM_CONTEXTS_BY_FAMILY.get(market_family, []):
            team_id = self._get_context_team_id(prop_context, context_rule["team_side"])
            if team_id is None:
                continue

            team_injuries = self.mlb_player_injuries_repository.get_injuries_for_team(team_id)
            relevant_injuries.extend(
                self._build_team_context_matches(
                    injuries=team_injuries,
                    expected_role=context_rule["expected_role"],
                    reason_template=context_rule["reason_template"],
                    relevance_type=context_rule["relevance_type"],
                    market_key=prop_context.market_key,
                    market_family=market_family,
                    team_side=context_rule["team_side"],
                )
            )

        return relevant_injuries

    def _build_direct_player_matches(
        self,
        injuries: list[MLBPlayerInjuries],
        market_family: str,
        prop_context: PropInjuryContext,
    ) -> list[RelevantInjuryContext]:
        expected_role = DIRECT_PLAYER_ROLE_BY_FAMILY[market_family]
        relevance_type = "direct_player_injury"
        reason = f"Prop player has a relevant {expected_role} injury for this market"

        return [
            self._to_relevant_injury_context(
                injury,
                relevance_reason=reason,
                metadata={
                    "market_family": market_family,
                    "market_key": prop_context.market_key,
                    "normalized_role": expected_role,
                    "relevance_type": relevance_type,
                    "context_side": "direct_player",
                },
            )
            for injury in injuries
            if self._is_relevant_injury(injury, expected_role)
        ]

    def _build_team_context_matches(
        self,
        injuries: list[MLBPlayerInjuries],
        expected_role: str,
        reason_template: str,
        relevance_type: str,
        market_key: str,
        market_family: str,
        team_side: str,
    ) -> list[RelevantInjuryContext]:
        return [
            self._to_relevant_injury_context(
                injury,
                relevance_reason=reason_template,
                metadata={
                    "market_family": market_family,
                    "market_key": market_key,
                    "normalized_role": expected_role,
                    "relevance_type": relevance_type,
                    "context_side": team_side,
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

    def _get_same_team_id(self, prop_context: PropInjuryContext) -> int | None:
        return prop_context.player_team_id

    def _get_context_team_id(self, prop_context: PropInjuryContext, team_side: str) -> int | None:
        if team_side == "opposing":
            return self._get_opposing_team_id(prop_context)
        if team_side == "same":
            return self._get_same_team_id(prop_context)
        return None

    def _classify_market_family(self, market_key: str) -> str | None:
        return MARKET_FAMILIES.get(market_key)

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