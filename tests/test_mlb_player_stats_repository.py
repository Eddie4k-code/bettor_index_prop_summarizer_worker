from datetime import datetime, timedelta

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from db.models.base import Base
from db.models.mlb_player_stats import MLBPlayerStats
from repositories.mlb_player_stats_repository import MLBPlayerStatsRepository


@pytest.fixture(scope="function")
def db_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine)()
    yield session
    session.close()
    engine.dispose()


@pytest.fixture(scope="function")
def mlb_player_stats_repo(db_session):
    start = datetime(2026, 6, 1, 12, 0, 0)
    db_session.add_all(
        [
            MLBPlayerStats(
                player_id=77,
                first_name="Aaron",
                last_name="Judge",
                team_name="Yankees",
                game_id=1,
                season=2026,
                hits=2,
                total_bases=4,
                sport_key="baseball_mlb",
                commence_time=start,
            ),
            MLBPlayerStats(
                player_id=77,
                first_name="Aaron",
                last_name="Judge",
                team_name="Yankees",
                game_id=2,
                season=2026,
                hits=1,
                total_bases=2,
                sport_key="baseball_mlb",
                commence_time=start + timedelta(days=1),
            ),
            MLBPlayerStats(
                player_id=77,
                first_name="Aaron",
                last_name="Judge",
                team_name="Yankees",
                game_id=3,
                season=2026,
                hits=3,
                total_bases=5,
                sport_key="baseball_mlb",
                commence_time=start + timedelta(days=2),
            ),
            MLBPlayerStats(
                player_id=99,
                first_name="Juan",
                last_name="Soto",
                team_name="Yankees",
                game_id=4,
                season=2026,
                hits=1,
                total_bases=1,
                sport_key="baseball_mlb",
                commence_time=start + timedelta(days=3),
            ),
        ]
    )
    db_session.commit()
    return MLBPlayerStatsRepository(db_session)


def test_get_player_stats_returns_all_rows_in_descending_time_order(mlb_player_stats_repo):
    results = mlb_player_stats_repo.get_player_stats(77)

    assert [row["game_id"] for row in results] == [3, 2, 1]
    assert all(row["player_id"] == 77 for row in results)


def test_get_recent_player_stats_limits_results(mlb_player_stats_repo):
    results = mlb_player_stats_repo.get_recent_player_stats(77, limit=2)

    assert [row["game_id"] for row in results] == [3, 2]
    assert len(results) == 2