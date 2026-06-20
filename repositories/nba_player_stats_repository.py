
from typing import List
from sqlalchemy.orm import Session
from db.models.nba_player_stats import NBAPlayerStats
from interfaces.nba_player_stats_repository_interface import NBAPlayerStatsRepositoryInterface

class NBAPlayerStatsRepository(NBAPlayerStatsRepositoryInterface):
    def __init__(self, db_session: Session):
        self.db_session = db_session

    def get_player_stats(self, player_id: int) -> List[dict]:
        results = self._player_stats_query(player_id).all()
        return [self._to_dict(r) for r in results]

    def get_recent_player_stats(self, player_id: int, limit: int) -> List[dict]:
        results = self._player_stats_query(player_id).limit(limit).all()
        return [self._to_dict(r) for r in results]

    def _player_stats_query(self, player_id: int):
        return (
            self.db_session.query(NBAPlayerStats)
            .filter(NBAPlayerStats.player_id == player_id)
            .order_by(NBAPlayerStats.commence_time.desc())
        )

    def _to_dict(self, obj) -> dict:
        return {c.name: getattr(obj, c.name) for c in obj.__table__.columns}