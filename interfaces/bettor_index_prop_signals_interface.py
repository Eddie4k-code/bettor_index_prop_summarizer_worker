from abc import ABC, abstractmethod
from typing import Any


class IBettorIndexPropSignalsService(ABC):
    @abstractmethod
    def build_signal(
        self,
        best_over_line: dict[str, Any] | None,
        best_under_line: dict[str, Any] | None,
        best_over_price: dict[str, Any] | None,
        best_under_price: dict[str, Any] | None,
        line_discrepancy_over: dict[str, Any] | str | None,
    ) -> dict[str, Any]:
        """Build a bettor-facing lean signal for a summary payload."""
