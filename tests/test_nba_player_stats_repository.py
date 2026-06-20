from datetime import datetime, timedelta

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from db.models.base import Base
from db.models.nba_player_stats import NBAPlayerStats
from repositories.nba_player_stats_repository import NBAPlayerStatsRepository


@pytest.fixture(scope="function")
def db_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine)()
    yield session
    session.close()
    engine.dispose()


@pytest.fixture(scope="function")
def nba_player_stats_repo(db_session):
    start = datetime(2026, 6, 1, 19, 0, 0)
    db_session.add_all(
        [
            NBAPlayerStats(
                player_id=23,
                first_name="LeBron",
                last_name="James",
                team_id=14,
                game_id=10,
                season=2026,
                points=24,
                assists=8,
                totReb=7,
                sport_key="basketball_nba",
                commence_time=start,
            ),
            NBAPlayerStats(
                player_id=23,
                first_name="LeBron",
                last_name="James",
                team_id=14,
                game_id=11,
                season=2026,
                points=28,
                assists=10,
                totReb=9,
                sport_key="basketball_nba",
                commence_time=start + timedelta(days=1),
            ),
            NBAPlayerStats(
                player_id=23,
                first_name="LeBron",
                last_name="James",
                team_id=14,
                game_id=12,
                season=2026,
                points=30,
                assists=11,
                totReb=8,
                sport_key="basketball_nba",
                commence_time=start + timedelta(days=2),
            ),
            NBAPlayerStats(
                player_id=7,
                first_name="Jayson",
                last_name="Tatum",
                team_id=2,
                game_id=13,
                season=2026,
                points=26,
                assists=4,
                totReb=6,
                sport_key="basketball_nba",
                commence_time=start + timedelta(days=3),
            ),
        ]
    )
    db_session.commit()
    return NBAPlayerStatsRepository(db_session)


def test_get_player_stats_returns_all_rows_in_descending_time_order(nba_player_stats_repo):
    results = nba_player_stats_repo.get_player_stats(23)

    assert [row["game_id"] for row in results] == [12, 11, 10]
    assert all(row["player_id"] == 23 for row in results)


def test_get_recent_player_stats_limits_results(nba_player_stats_repo):
    results = nba_player_stats_repo.get_recent_player_stats(23, limit=2)

    assert [row["game_id"] for row in results] == [12, 11]
    assert len(results) == 2