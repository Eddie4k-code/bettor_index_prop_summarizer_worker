from typing import List
from db.models.hit_rate_summarizer_event_queue import HitRateSummarizerQueue
from interfaces.hit_rate_summarizer_event_queue_repository import IHitRateSummarizerEventQueueRepository

class HitRateSummarizerEventQueueRepository(IHitRateSummarizerEventQueueRepository):
    def __init__(self, DB):
        self.DB = DB

    def fetch_pending_events(self, batch_size: int) -> List[HitRateSummarizerQueue]:
        return (
            self.DB.query(HitRateSummarizerQueue)
            .filter(HitRateSummarizerQueue.status == 'pending')
            .limit(batch_size)
            .all()
        )

    def mark_event_consumed(self, event: HitRateSummarizerQueue) -> None:
        event.status = 'consumed'
        self.DB.add(event)
        self.DB.commit()
