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