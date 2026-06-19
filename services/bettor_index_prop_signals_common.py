from typing import Any

STRONG_RECENT_EDGE = 0.15
MEDIUM_RECENT_EDGE = 0.08
WEAK_RECENT_EDGE = 0.04
STRONG_VALUE_EDGE = 0.04
MEDIUM_VALUE_EDGE = 0.01
HIGH_JUICE_IMPLIED_PROBABILITY = 0.65
VERY_HIGH_JUICE_IMPLIED_PROBABILITY = 0.7
HIGH_JUICE_VALUE_EDGE = 0.03


def is_finite_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and value == value and value not in (float("inf"), float("-inf"))


def normalize_trend_windows(
    line: dict[str, Any] | None,
    window_configs: list[dict[str, str | float]],
) -> list[dict[str, Any]]:
    if not line:
        return []

    windows: list[dict[str, Any]] = []
    for config in window_configs:
        value = line.get(config["key"])
        if not is_finite_number(value):
            continue

        windows.append(
            {
                "label": config["label"],
                "value": float(value),
                "weight": float(config["weight"]),
            }
        )

    return windows


def get_weighted_rate(trend_windows: list[dict[str, Any]]) -> float | None:
    weighted_total = 0.0
    total_weight = 0.0

    for window in trend_windows:
        value = window.get("value")
        weight = window.get("weight")
        if not is_finite_number(value) or not is_finite_number(weight):
            continue

        weighted_total += float(value) * float(weight)
        total_weight += float(weight)

    if total_weight == 0:
        return None

    return weighted_total / total_weight


def parse_american_odds(value: Any) -> float | None:
    if is_finite_number(value):
        return float(value)

    if isinstance(value, str):
        normalized = "".join(character for character in value if character.isdigit() or character in "+-")
        if not normalized:
            return None
        try:
            parsed = float(normalized)
        except ValueError:
            return None
        return parsed if is_finite_number(parsed) else None

    return None


def to_implied_probability(price: Any) -> float | None:
    american_odds = parse_american_odds(price)
    if american_odds is None or american_odds == 0:
        return None

    if american_odds > 0:
        return 100 / (american_odds + 100)

    absolute_odds = abs(american_odds)
    return absolute_odds / (absolute_odds + 100)


def get_market_state(discrepancy: dict[str, Any] | str | None) -> str:
    if not discrepancy:
        return "unknown"
    if discrepancy == "No line discrepancy":
        return "books_agree"
    return "books_disagree"


def get_required_value_edge(selected_implied_probability: float | None) -> float:
    if selected_implied_probability is None:
        return MEDIUM_VALUE_EDGE
    if selected_implied_probability >= VERY_HIGH_JUICE_IMPLIED_PROBABILITY:
        return STRONG_VALUE_EDGE
    if selected_implied_probability >= HIGH_JUICE_IMPLIED_PROBABILITY:
        return HIGH_JUICE_VALUE_EDGE
    return MEDIUM_VALUE_EDGE


def get_strength(recent_edge_abs: float, selected_value_edge: float | None) -> str:
    if recent_edge_abs < WEAK_RECENT_EDGE:
        return "none"
    if recent_edge_abs >= STRONG_RECENT_EDGE and (selected_value_edge is None or selected_value_edge >= STRONG_VALUE_EDGE):
        return "strong"
    if recent_edge_abs >= MEDIUM_RECENT_EDGE and (selected_value_edge is None or selected_value_edge >= MEDIUM_VALUE_EDGE):
        return "medium"
    return "weak"


def get_action(
    side: str,
    market_state: str,
    selected_value_edge: float | None,
    selected_implied_probability: float | None,
) -> str:
    if side == "NONE":
        return "pass"
    if market_state == "books_disagree":
        return "shop_line"
    if selected_value_edge is not None and selected_value_edge < 0:
        return "pass"
    if selected_implied_probability is not None and selected_implied_probability >= VERY_HIGH_JUICE_IMPLIED_PROBABILITY:
        return "shop_price"
    if selected_value_edge is not None and selected_value_edge >= get_required_value_edge(selected_implied_probability):
        return "bet_now"
    return "shop_price"


def build_signal_payload(
    best_over_line: dict[str, Any] | None,
    best_under_line: dict[str, Any] | None,
    best_over_price: dict[str, Any] | None,
    best_under_price: dict[str, Any] | None,
    line_discrepancy_over: dict[str, Any] | str | None,
    window_configs: list[dict[str, str | float]],
) -> dict[str, Any]:
    over_trend_windows = normalize_trend_windows(best_over_line, window_configs)
    under_trend_windows = normalize_trend_windows(best_under_line, window_configs)
    weighted_over_rate = get_weighted_rate(over_trend_windows)
    weighted_under_rate = get_weighted_rate(under_trend_windows)
    expected_window_labels = [str(config["label"]) for config in window_configs]
    available_over_window_labels = [str(window["label"]) for window in over_trend_windows]
    available_under_window_labels = [str(window["label"]) for window in under_trend_windows]

    recent_edge = None
    if weighted_over_rate is not None and weighted_under_rate is not None:
        recent_edge = weighted_under_rate - weighted_over_rate

    if recent_edge is None or abs(recent_edge) < WEAK_RECENT_EDGE:
        side = "NONE"
    elif recent_edge > 0:
        side = "UNDER"
    else:
        side = "OVER"

    over_implied_probability = to_implied_probability(best_over_price.get("outcome_price") if best_over_price else None)
    under_implied_probability = to_implied_probability(best_under_price.get("outcome_price") if best_under_price else None)

    selected_estimated_rate = None
    selected_implied_probability = None
    if side == "UNDER":
        selected_estimated_rate = weighted_under_rate
        selected_implied_probability = under_implied_probability
    elif side == "OVER":
        selected_estimated_rate = weighted_over_rate
        selected_implied_probability = over_implied_probability

    selected_value_edge = None
    if selected_estimated_rate is not None and selected_implied_probability is not None:
        selected_value_edge = selected_estimated_rate - selected_implied_probability

    market_state = get_market_state(line_discrepancy_over)
    recent_edge_abs = abs(recent_edge) if recent_edge is not None else 0.0
    strength = "none" if side == "NONE" else get_strength(recent_edge_abs, selected_value_edge)
    action = get_action(side, market_state, selected_value_edge, selected_implied_probability)

    return {
        "side": side,
        "strength": strength,
        "action": action,
        "market_state": market_state,
        "expected_trend_windows": expected_window_labels,
        "over_trend_windows": over_trend_windows,
        "under_trend_windows": under_trend_windows,
        "available_over_trend_windows": available_over_window_labels,
        "available_under_trend_windows": available_under_window_labels,
        "weighted_over_rate": weighted_over_rate,
        "weighted_under_rate": weighted_under_rate,
        "recent_edge": recent_edge,
        "over_implied_probability": over_implied_probability,
        "under_implied_probability": under_implied_probability,
        "selected_value_edge": selected_value_edge,
    }
