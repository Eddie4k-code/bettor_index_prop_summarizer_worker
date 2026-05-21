from interfaces.summarizer_worker_interface import ISummarizerWorker
from interfaces.summarizer_interface import ISummarizerInterface
from interfaces.hit_rate_summarizer_event_queue_repository import IHitRateSummarizerEventQueueRepository
from db.models.hit_rate_summarizer_event_queue import HitRateSummarizerQueue
import logging

logger = logging.getLogger(__name__)

class SummarizerWorker(ISummarizerWorker):
    def __init__(self, nba_summarizer: ISummarizerInterface, hit_rate_summarizer_event_queue_repository: IHitRateSummarizerEventQueueRepository):
        self.nba_summarizer = nba_summarizer
        self.hit_rate_summarizer_event_queue_repository = hit_rate_summarizer_event_queue_repository

    def process_events(self, batch_size=10):
        """
        Fetch and process a batch of pending events from the hit rate summarizer event queue.
        Args:
            batch_size: Number of events to process at once.
        Returns:
            List of results from processing each event.
        """
        events: list[HitRateSummarizerQueue] = self.hit_rate_summarizer_event_queue_repository.fetch_pending_events(batch_size)
        results = []
        for event in events:
            # Extract relevant fields (adjust attribute names as needed)
            event_id = event.event_id
            market_key = event.market_key
            outcome_description = event.outcome_description

            # Pass to summarizer
            if event.sport_key == "basketball_nba":
            
                summary = self.nba_summarizer.summarize(event_id, market_key, outcome_description)
                results.append({
                    "event_id": event_id,
                    "summary": summary
                })

                # Mark event as consumed
                self.hit_rate_summarizer_event_queue_repository.mark_event_consumed(event)


    def store_summary(self, summary):
        """
        Store the generated summary in the appropriate location (e.g., database, file, etc.).
        Args:
            summary: The summary data to store.
        """
        # Implement storage logic here (e.g., save to database or file)
        pass

