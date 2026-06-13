import datetime

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from db.models.mlb_summaries import Base, MLBSummary
from repositories.mlb_summary_repository import MLBSummaryRepository


@pytest.fixture
def session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    return Session()


@pytest.fixture
def repo(session):
    return MLBSummaryRepository(session)


def make_summary(event_id="evt1", market_key="hits", outcome_description="Aaron Judge", sport_key="baseball_mlb"):
    return MLBSummary(
        event_id=event_id,
        market_key=market_key,
        outcome_description=outcome_description,
        commence_time=datetime.datetime.utcnow(),
        home_team="NYY",
        away_team="BOS",
        summary_data={"foo": "bar"},
        sport_key=sport_key,
    )


def test_insert_summary_inserts_and_commits(repo, session):
    summary = make_summary()
    repo.insert_summary(summary)

    found = session.query(MLBSummary).filter_by(event_id="evt1", market_key="hits", outcome_description="Aaron Judge").first()
    assert found is not None
    assert found.home_team == "NYY"


def test_insert_summary_updates_existing(repo, session):
    summary = make_summary()
    repo.insert_summary(summary)

    summary.home_team = "LAD"
    repo.insert_summary(summary)

    found = session.query(MLBSummary).filter_by(event_id="evt1", market_key="hits", outcome_description="Aaron Judge").first()
    assert found.home_team == "LAD"