from typing import Optional

from sqlalchemy.orm import Session

from db.models.teams import Team
from interfaces.team_repository_interface import TeamRepositoryInterface


class TeamRepository(TeamRepositoryInterface):
    def __init__(self, db_session: Session):
        self.db_session = db_session

    def get_team_by_id(self, team_id: int, sport_key: str) -> Optional[Team]:
        return (
            self.db_session.query(Team)
            .filter(Team.id == team_id, Team.sport_key == sport_key)
            .first()
        )