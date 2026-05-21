from abc import ABC, abstractmethod

class ISummarizerWorker(ABC):
    @abstractmethod
    def process_events(self):
        """
        Process events from the hit rate summarizer event queue.
        Returns:
            Any result or status from processing the event.
        """
        pass
    
    @abstractmethod
    def store_summary(self, summary):
        """
        Store the generated summary in the appropriate location (e.g., database, file, etc.).
        Args:
            summary: The summary data to store.
        """
        pass