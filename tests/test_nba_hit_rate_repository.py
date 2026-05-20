import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from db.models.base import Base
from db.models.nba_hit_rates import NBAHitRates
from repositories.nba_hit_rate_repository import NBAHitRatesRepository

@pytest.fixture(scope="function")
def db_session():
    engine = create_engine('sqlite:///:memory:')
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    db = Session()
    yield db
    db.close()
    engine.dispose()

@pytest.fixture(scope="function")
def nba_hit_rates_repo(db_session):
    repo = NBAHitRatesRepository(db_session)
    # Insert test data
    db_session.add_all([
        NBAHitRates(
            event_id='1', bookmaker='bm1', market_key='A', outcome_description='desc1', outcome_name='outcome1',
            commence_time='2026-05-19T00:00:00Z', player_id=101, season=2026, sport_key='basketball.nba',
            ten_game_hit_rate=0.5, thirty_game_hit_rate=0.6, sixty_game_hit_rate=0.7, outcome_point='10.5',
            outcome_price='-110', market_last_update='2026-05-19T00:00:00Z', home_team='Lakers'
        ),
        NBAHitRates(
            event_id='1', bookmaker='bm2', market_key='A', outcome_description='desc1', outcome_name='outcome2',
            commence_time='2026-05-19T00:00:00Z', player_id=102, season=2026, sport_key='basketball.nba',
            ten_game_hit_rate=0.55, thirty_game_hit_rate=0.65, sixty_game_hit_rate=0.75, outcome_point='11.5',
            outcome_price='-105', market_last_update='2026-05-19T00:00:00Z', home_team='Lakers'
        ),
        NBAHitRates(
            event_id='1', bookmaker='bm1', market_key='B', outcome_description='desc2', outcome_name='outcome3',
            commence_time='2026-05-19T00:00:00Z', player_id=103, season=2026, sport_key='basketball.nba',
            ten_game_hit_rate=0.6, thirty_game_hit_rate=0.7, sixty_game_hit_rate=0.8, outcome_point='12.5',
            outcome_price='-120', market_last_update='2026-05-19T00:00:00Z', home_team='Celtics'
        ),
        NBAHitRates(
            event_id='2', bookmaker='bm1', market_key='A', outcome_description='desc1', outcome_name='outcome1',
            commence_time='2026-05-19T00:00:00Z', player_id=104, season=2026, sport_key='basketball.nba',
            ten_game_hit_rate=0.65, thirty_game_hit_rate=0.75, sixty_game_hit_rate=0.85, outcome_point='13.5',
            outcome_price='-115', market_last_update='2026-05-19T00:00:00Z', home_team='Warriors'
        ),
    ])
    db_session.commit()
    return repo

def test_get_hit_rates_by_keys(nba_hit_rates_repo):
    results = nba_hit_rates_repo.get_hit_rates_by_keys('1', 'A', 'desc1')
    assert len(results) == 2
    for hit_rate in results:
        assert hit_rate.event_id == '1'
        assert hit_rate.market_key == 'A'
        assert hit_rate.outcome_description == 'desc1'
