import logging

from db.models.mlb_summaries import MLBSummary
from interfaces.mlb_summary_repository_interface import IMLBSummaryRepository


logger = logging.getLogger(__name__)


class MLBSummaryRepository(IMLBSummaryRepository):
    def __init__(self, DB):
        self.DB = DB

    def insert_summary(self, summary: MLBSummary):
        """
        Insert or update an MLB summary in the database.
        Args:
            summary: MLBSummary instance.
        """
        try:
            self.DB.merge(summary)
            self.DB.commit()
        except Exception as e:
            logger.error(f"Error inserting MLB summary: {e}")
            self.DB.rollback()