import pytest

from services.mlb_bettor_index_prop_signals_service import MLBBettorIndexPropSignalsService
from services.nba_bettor_index_prop_signals_service import NBABettorIndexPropSignalsService


def test_mlb_signal_renormalizes_when_sixty_game_window_missing():
    service = MLBBettorIndexPropSignalsService()

    signal = service.build_signal(
        best_over_line={
            "ten_game_hit_rate": 0.45,
            "thirty_game_hit_rate": 0.4,
        },
        best_under_line={
            "ten_game_hit_rate": 0.7,
            "thirty_game_hit_rate": 0.6,
        },
        best_over_price={"outcome_price": 110},
        best_under_price={"outcome_price": -105},
        line_discrepancy_over="No line discrepancy",
    )

    assert signal["expected_trend_windows"] == ["10D", "30D", "60D"]
    assert signal["available_over_trend_windows"] == ["10D", "30D"]
    assert signal["available_under_trend_windows"] == ["10D", "30D"]
    assert signal["weighted_over_rate"] == pytest.approx(0.43125)
    assert signal["weighted_under_rate"] == pytest.approx(0.6625)
    assert signal["side"] == "UNDER"
    assert signal["strength"] == "strong"
    assert signal["lean_label"] == "Strong Lean Under"
    assert signal["market_label"] == "Opportunity"
    assert signal["reason_code"] == "positive_edge_current_price"
    assert signal["reason_text"] == "Backend sees a strong under trend with positive edge at the current best price."


def test_nba_signal_can_use_sport_specific_window_config():
    service = NBABettorIndexPropSignalsService(
        window_configs=[
            {"key": "ten_game_hit_rate", "label": "10D", "weight": 0.7},
            {"key": "thirty_game_hit_rate", "label": "30D", "weight": 0.3},
        ]
    )

    signal = service.build_signal(
        best_over_line={
            "ten_game_hit_rate": 0.48,
            "thirty_game_hit_rate": 0.5,
            "sixty_game_hit_rate": 0.9,
        },
        best_under_line={
            "ten_game_hit_rate": 0.62,
            "thirty_game_hit_rate": 0.58,
            "sixty_game_hit_rate": 0.1,
        },
        best_over_price={"outcome_price": 105},
        best_under_price={"outcome_price": -102},
        line_discrepancy_over={"discrepancy": 1.0},
    )

    assert signal["expected_trend_windows"] == ["10D", "30D"]
    assert signal["available_over_trend_windows"] == ["10D", "30D"]
    assert signal["available_under_trend_windows"] == ["10D", "30D"]
    assert signal["weighted_over_rate"] == pytest.approx(0.486)
    assert signal["weighted_under_rate"] == pytest.approx(0.608)
    assert signal["market_state"] == "books_disagree"
    assert signal["action"] == "shop_line"
    assert signal["strength"] == "medium"
    assert signal["lean_label"] == "Lean Under"
    assert signal["market_label"] == "Worth Watching"
    assert signal["reason_code"] == "books_disagree"
    assert signal["reason_text"] == "Backend sees a clear under trend, but books are not aligned on the current market."


def test_signal_marks_potential_pass_when_no_strong_trend_exists():
    service = MLBBettorIndexPropSignalsService()

    signal = service.build_signal(
        best_over_line={
            "ten_game_hit_rate": 0.51,
            "thirty_game_hit_rate": 0.49,
        },
        best_under_line={
            "ten_game_hit_rate": 0.5,
            "thirty_game_hit_rate": 0.48,
        },
        best_over_price={"outcome_price": -102},
        best_under_price={"outcome_price": -102},
        line_discrepancy_over="No line discrepancy",
    )

    assert signal["side"] == "NONE"
    assert signal["strength"] == "none"
    assert signal["action"] == "pass"
    assert signal["lean_label"] == "No Strong Lean"
    assert signal["market_label"] == "Potential Pass"
    assert signal["reason_code"] == "no_strong_trend"
    assert signal["reason_text"] == "Backend does not see a strong over or under trend right now."