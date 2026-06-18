import logging

from db.models.mlb_player_injuries import MLBPlayerInjuries
from interfaces.mlb_player_injuries_repository_interface import IMLBPlayerInjuriesRepository


logger = logging.getLogger(__name__)


class MLBPlayerInjuriesRepository(IMLBPlayerInjuriesRepository):
    def __init__(self, db_session):
        self.DB = db_session

    def get_injuries_for_team(self, team_id: int) -> list[MLBPlayerInjuries]:
        try:
            return (
                self.DB.query(MLBPlayerInjuries)
                .filter(MLBPlayerInjuries.team_id == team_id)
                .order_by(MLBPlayerInjuries.date.desc(), MLBPlayerInjuries.player_id.asc())
                .all()
            )
        except Exception as exc:
            logger.error("Error fetching MLB injuries for team_id %s: %s", team_id, exc)
            return []

    def get_injuries_for_player(self, player_id: int) -> list[MLBPlayerInjuries]:
        try:
            return (
                self.DB.query(MLBPlayerInjuries)
                .filter(MLBPlayerInjuries.player_id == player_id)
                .order_by(MLBPlayerInjuries.date.desc(), MLBPlayerInjuries.team_id.asc())
                .all()
            )
        except Exception as exc:
            logger.error("Error fetching MLB injuries for player_id %s: %s", player_id, exc)
            return []