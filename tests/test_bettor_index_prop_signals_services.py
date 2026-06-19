from services.mlb_bettor_index_prop_signals_service import MLBBettorIndexPropSignalsService
from services.nba_bettor_index_prop_signals_service import NBABettorIndexPropSignalsService


def test_mlb_signal_service_uses_default_windows():
    service = MLBBettorIndexPropSignalsService()

    signal = service.build_signal(
        best_over_line={
            "ten_game_hit_rate": 0.65,
            "thirty_game_hit_rate": 0.55,
            "sixty_game_hit_rate": 0.5,
        },
        best_under_line={
            "ten_game_hit_rate": 0.35,
            "thirty_game_hit_rate": 0.45,
            "sixty_game_hit_rate": 0.5,
        },
        best_over_price={"outcome_price": 110},
        best_under_price={"outcome_price": -105},
        line_discrepancy_over="No line discrepancy",
    )

    assert [window["label"] for window in signal["over_trend_windows"]] == ["10D", "30D", "60D"]


def test_nba_signal_service_accepts_sport_specific_windows():
    service = NBABettorIndexPropSignalsService(
        window_configs=[
            {"key": "five_game_hit_rate", "label": "5G", "weight": 0.6},
            {"key": "fifteen_game_hit_rate", "label": "15G", "weight": 0.4},
        ]
    )

    signal = service.build_signal(
        best_over_line={
            "five_game_hit_rate": 0.7,
            "fifteen_game_hit_rate": 0.6,
        },
        best_under_line={
            "five_game_hit_rate": 0.3,
            "fifteen_game_hit_rate": 0.4,
        },
        best_over_price={"outcome_price": 105},
        best_under_price={"outcome_price": -110},
        line_discrepancy_over={"discrepancy": 1.0},
    )

    assert [window["label"] for window in signal["over_trend_windows"]] == ["5G", "15G"]
    assert signal["weighted_over_rate"] == 0.6599999999999999
    assert signal["market_state"] == "books_disagree"