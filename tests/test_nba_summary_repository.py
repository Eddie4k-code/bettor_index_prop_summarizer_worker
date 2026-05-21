import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from db.models.nba_summaries import Base, NBASummary
from repositories.nba_summary_repository import NBASummaryRepository
import datetime

@pytest.fixture
def session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    return Session()

@pytest.fixture
def repo(session):
    return NBASummaryRepository(session)

def make_summary(event_id="evt1", market_key="points", outcome_description="over", sport_key="basketball_nba"):
    return NBASummary(
        event_id=event_id,
        market_key=market_key,
        outcome_description=outcome_description,
        commence_time=datetime.datetime.utcnow(),
        home_team="A",
        away_team="B",
        summary_data={"foo": "bar"},
        sport_key=sport_key
    )

def test_insert_summary_inserts_and_commits(repo, session):
    summary = make_summary()
    repo.insert_summary(summary)
    found = session.query(NBASummary).filter_by(event_id="evt1", market_key="points", outcome_description="over").first()
    assert found is not None
    assert found.home_team == "A"

def test_insert_summary_updates_existing(repo, session):
    summary = make_summary()
    repo.insert_summary(summary)
    # Update and re-insert
    summary.home_team = "C"
    repo.insert_summary(summary)
    found = session.query(NBASummary).filter_by(event_id="evt1", market_key="points", outcome_description="over").first()
    assert found.home_team == "C"
