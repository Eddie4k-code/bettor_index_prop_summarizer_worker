from typing import List

from sqlalchemy.orm import Session

from db.models.mlb_player_stats import MLBPlayerStats
from interfaces.mlb_player_stats_repository_interface import MLBPlayerStatsRepositoryInterface


class MLBPlayerStatsRepository(MLBPlayerStatsRepositoryInterface):
    def __init__(self, db_session: Session):
        self.db_session = db_session

    def get_player_stats(self, player_id: int) -> List[dict]:
        results = (
            self.db_session.query(MLBPlayerStats)
            .filter(MLBPlayerStats.player_id == player_id)
            .order_by(MLBPlayerStats.commence_time.desc())
            .all()
        )
        return [self._to_dict(result) for result in results]

    def _to_dict(self, obj) -> dict:
        return {column.name: getattr(obj, column.name) for column in obj.__table__.columns}