from abc import ABC, abstractmethod
from typing import List
from db.models.hit_rate_summarizer_event_queue import HitRateSummarizerQueue

class IHitRateSummarizerEventQueueRepository(ABC):
    @abstractmethod
    def fetch_pending_events(self, batch_size: int) -> List[HitRateSummarizerQueue]:
        pass

    @abstractmethod
    def mark_event_consumed(self, event: HitRateSummarizerQueue) -> None:
        pass
