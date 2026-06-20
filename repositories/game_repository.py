from typing import Optional

from sqlalchemy.orm import Session

from db.models.games import Game
from interfaces.game_repository_interface import GameRepositoryInterface


class GameRepository(GameRepositoryInterface):
    def __init__(self, db_session: Session):
        self.db_session = db_session

    def get_game_by_id(self, game_id: int, sport_key: str) -> Optional[Game]:
        return (
            self.db_session.query(Game)
            .filter(Game.id == game_id, Game.sport_key == sport_key)
            .first()
        )