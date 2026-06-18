import datetime

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from db.models.mlb_player_injuries import Base, MLBPlayerInjuries
from repositories.mlb_player_injuries_repository import MLBPlayerInjuriesRepository


def build_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine)()
    return session


def seed_injuries(session):
    injuries = [
        MLBPlayerInjuries(
            player_id=101,
            team_id=1,
            date=datetime.datetime(2026, 6, 1),
            return_date=None,
            display_name="Pitcher A",
            type="shoulder",
            detail="starter",
            side="right",
            status="out",
            long_comment="long",
            short_comment="short",
        ),
        MLBPlayerInjuries(
            player_id=202,
            team_id=2,
            date=datetime.datetime(2026, 6, 2),
            return_date=None,
            display_name="Batter B",
            type="hamstring",
            detail="bench",
            side="left",
            status="day-to-day",
            long_comment="long",
            short_comment="short",
        ),
        MLBPlayerInjuries(
            player_id=101,
            team_id=2,
            date=datetime.datetime(2026, 6, 3),
            return_date=None,
            display_name="Pitcher A",
            type="elbow",
            detail="duplicate player on another team entry",
            side="right",
            status="out",
            long_comment="long",
            short_comment="short",
        ),
    ]
    session.add_all(injuries)
    session.commit()


def test_get_injuries_for_team_returns_matching_rows():
    session = build_session()
    seed_injuries(session)
    repo = MLBPlayerInjuriesRepository(session)

    injuries = repo.get_injuries_for_team(1)

    assert [injury.player_id for injury in injuries] == [101]
    assert injuries[0].display_name == "Pitcher A"


def test_get_injuries_for_player_returns_matching_rows():
    session = build_session()
    seed_injuries(session)
    repo = MLBPlayerInjuriesRepository(session)

    injuries = repo.get_injuries_for_player(101)

    assert len(injuries) == 2
    assert all(injury.player_id == 101 for injury in injuries)
    assert injuries[0].date >= injuries[1].date