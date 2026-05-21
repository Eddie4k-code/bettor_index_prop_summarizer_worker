from interfaces.summarizer_worker_interface import ISummarizerWorker
from interfaces.summarizer_interface import ISummarizerInterface
from interfaces.hit_rate_summarizer_event_queue_repository import IHitRateSummarizerEventQueueRepository
from db.models.hit_rate_summarizer_event_queue import HitRateSummarizerQueue
import logging
from interfaces.nba_summary_repository_interface import INBASummaryRepository
from db.models.nba_summaries import NBASummary

logger = logging.getLogger(__name__)

class SummarizerWorker(ISummarizerWorker):
    def __init__(self, nba_summarizer: ISummarizerInterface, hit_rate_summarizer_event_queue_repository: IHitRateSummarizerEventQueueRepository, nba_summary_repository: INBASummaryRepository):
        self.nba_summarizer = nba_summarizer
        self.hit_rate_summarizer_event_queue_repository = hit_rate_summarizer_event_queue_repository
        self.nba_summary_repository = nba_summary_repository

    def process_events(self, batch_size=10):
        """
        Fetch and process a batch of pending events from the hit rate summarizer event queue.
        Args:
            batch_size: Number of events to process at once.
        Returns:
            List of results from processing each event.
        """
        events: list[HitRateSummarizerQueue] = self.hit_rate_summarizer_event_queue_repository.fetch_pending_events(batch_size)
        for event in events:
            # Extract relevant fields (adjust attribute names as needed)
            event_id = event.event_id
            market_key = event.market_key
            outcome_description = event.outcome_description

            # Pass to summarizer for NBA
            if event.sport_key == "basketball_nba":
            
                summary = self.nba_summarizer.summarize(event_id, market_key, outcome_description)
    
                # Mark event as consumed
                self.hit_rate_summarizer_event_queue_repository.mark_event_consumed(event)

                # Store summary in database
                nba_summary = NBASummary(
                    event_id=summary["market"]["event_id"],
                    market_key=summary["market"]["market_key"],
                    outcome_description=summary["market"]["outcome_description"],
                    commence_time=summary["market"]["commence_time"],
                    home_team=summary["market"]["home_team"],
                    away_team=summary["market"]["away_team"],
                    summary_data=summary,
                    sport_key = summary["market"]["sport_key"]
                )

                self.nba_summary_repository.insert_summary(nba_summary)
