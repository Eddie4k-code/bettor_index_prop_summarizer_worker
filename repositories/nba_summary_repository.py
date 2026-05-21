from interfaces.nba_summary_repository_interface import INBASummaryRepository
from db.models.nba_summaries import NBASummary
import logging


logger = logging.getLogger(__name__)

class NBASummaryRepository(INBASummaryRepository):
    def __init__(self, DB):
        self.DB = DB

    def insert_summary(self, summary: NBASummary):
        """
        Insert or update an NBA summary in the database.
        Args:
            summary: NBASummary instance.
        """
        try:
            self.DB.merge(summary)  # merge will insert or update based on PK
            self.DB.commit()
        except Exception as e:
            logger.error(f"Error inserting NBA summary: {e}")
            self.DB.rollback()
