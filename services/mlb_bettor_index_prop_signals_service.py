from typing import Any

from interfaces.bettor_index_prop_signals_interface import IBettorIndexPropSignalsService
from services.bettor_index_prop_signals_common import build_signal_payload


class MLBBettorIndexPropSignalsService(IBettorIndexPropSignalsService):
    DEFAULT_WINDOW_CONFIGS: list[dict[str, str | float]] = [
        {"key": "ten_game_hit_rate", "label": "10D", "weight": 0.5},
        {"key": "thirty_game_hit_rate", "label": "30D", "weight": 0.3},
        {"key": "sixty_game_hit_rate", "label": "60D", "weight": 0.2},
    ]

    def __init__(self, window_configs: list[dict[str, str | float]] | None = None):
        self.window_configs = window_configs or self.DEFAULT_WINDOW_CONFIGS

    def build_signal(
        self,
        best_over_line: dict[str, Any] | None,
        best_under_line: dict[str, Any] | None,
        best_over_price: dict[str, Any] | None,
        best_under_price: dict[str, Any] | None,
        line_discrepancy_over: dict[str, Any] | str | None,
    ) -> dict[str, Any]:
        return build_signal_payload(
            best_over_line=best_over_line,
            best_under_line=best_under_line,
            best_over_price=best_over_price,
            best_under_price=best_under_price,
            line_discrepancy_over=line_discrepancy_over,
            window_configs=self.window_configs,
        )

