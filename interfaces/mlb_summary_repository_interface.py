from abc import ABC, abstractmethod

from db.models.mlb_summaries import MLBSummary


class IMLBSummaryRepository(ABC):
    @abstractmethod
    def insert_summary(self, summary: MLBSummary):
        """
        Insert or update an MLB summary in the database.
        Args:
            summary: MLBSummary instance.
        """
        pass