from typing import List

from sqlalchemy.orm import Session

from db.models.mlb_player_stats import MLBPlayerStats
from interfaces.mlb_player_stats_repository_interface import MLBPlayerStatsRepositoryInterface
from db.models.mlb_player_stats import MLBPlayerStats


class MLBPlayerStatsRepository(MLBPlayerStatsRepositoryInterface):
    def __init__(self, db_session: Session):
        self.db_session = db_session

    def get_player_stats(self, player_id: int) -> List[MLBPlayerStats]:
        results = self._player_stats_query(player_id).all()
        return results

    def get_recent_player_stats(self, player_id: int, limit: int) -> List[MLBPlayerStats]:
        results = self._player_stats_query(player_id).limit(limit).all()
        return results

    def _player_stats_query(self, player_id: int):
        return (
            self.db_session.query(MLBPlayerStats)
            .filter(MLBPlayerStats.player_id == player_id)
            .order_by(MLBPlayerStats.commence_time.desc())
        )

    def _to_dict(self, obj) -> dict:
        return {column.name: getattr(obj, column.name) for column in obj.__table__.columns}