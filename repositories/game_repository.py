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

    def get_games_by_ids(self, game_ids: list[int], sport_key: str) -> dict[int, Game]:
        if not game_ids:
            return {}

        games = (
            self.db_session.query(Game)
            .filter(Game.id.in_(game_ids), Game.sport_key == sport_key)
            .all()
        )

        return {game.id: game for game in games}

