from abc import ABC, abstractmethod
from db.models.nba_summaries import NBASummary

class INBASummaryRepository(ABC):
    @abstractmethod
    def insert_summary(self, summary: NBASummary):
        """
        Insert or update an NBA summary in the database.
        Args:
            summary: NBASummary instance.
        """
        pass
