from datetime import datetime

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from db.models.base import Base
from db.models.games import Game
from repositories.game_repository import GameRepository


@pytest.fixture(scope="function")
def db_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine)()
    yield session
    session.close()
    engine.dispose()


@pytest.fixture(scope="function")
def game_repo(db_session):
    db_session.add_all(
        [
            Game(
                id=100,
                season=2026,
                date=datetime(2026, 6, 1, 19, 0, 0),
                status="final",
                home_team="Lakers",
                home_team_id=14,
                away_team="Celtics",
                away_team_id=2,
                home_team_score=110,
                away_team_score=105,
                sport_key="basketball_nba",
            ),
            Game(
                id=101,
                season=2026,
                date=datetime(2026, 6, 2, 19, 0, 0),
                status="final",
                home_team="Yankees",
                home_team_id=10,
                away_team="Red Sox",
                away_team_id=20,
                home_team_score=5,
                away_team_score=2,
                sport_key="baseball_mlb",
            ),
        ]
    )
    db_session.commit()
    return GameRepository(db_session)


def test_get_game_by_id_returns_matching_game(game_repo):
    game = game_repo.get_game_by_id(100, "basketball_nba")

    assert game is not None
    assert game.home_team == "Lakers"
    assert game.away_team_id == 2


def test_get_games_by_ids_returns_games_keyed_by_id(game_repo):
    games = game_repo.get_games_by_ids([100, 101, 999], "basketball_nba")

    assert list(games.keys()) == [100]
    assert games[100].home_team == "Lakers"


def test_get_games_by_ids_returns_empty_dict_for_empty_input(game_repo):
    assert game_repo.get_games_by_ids([], "basketball_nba") == {}