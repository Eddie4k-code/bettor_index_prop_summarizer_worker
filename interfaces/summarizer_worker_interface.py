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