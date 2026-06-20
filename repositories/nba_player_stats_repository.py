
from typing import List
from sqlalchemy.orm import Session
from db.models.nba_player_stats import NBAPlayerStats
from interfaces.nba_player_stats_repository_interface import NBAPlayerStatsRepositoryInterface

class NBAPlayerStatsRepository(NBAPlayerStatsRepositoryInterface):
    def __init__(self, db_session: Session):
        self.db_session = db_session

    def get_player_stats(self, player_id: int) -> List[dict]:
        results = (
            self.db_session.query(NBAPlayerStats)
            .filter(NBAPlayerStats.player_id == player_id)
            .order_by(NBAPlayerStats.commence_time.desc())
            .all()
        )
        return [self._to_dict(r) for r in results]

    def _to_dict(self, obj) -> dict:
        return {c.name: getattr(obj, c.name) for c in obj.__table__.columns}