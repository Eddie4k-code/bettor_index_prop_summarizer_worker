import time
from db.db import get_db
from repositories.hit_rate_summarizer_event_queue_repository import HitRateSummarizerEventQueueRepository
from repositories.mlb_hit_rate_repository import MLBHitRatesRepository
from repositories.mlb_summary_repository import MLBSummaryRepository
from repositories.nba_summary_repository import NBASummaryRepository
from repositories.nba_hit_rate_repository import NBAHitRatesRepository
from summarizers.mlb_summarizer import MLBSummarizer
from summarizers.nba_summarizer import NBASummarizer
from worker.summarizer_worker import SummarizerWorker
from db.models.base import Base
from db.db import engine
import logging

logger = logging.getLogger(__name__)

logging.basicConfig(level=logging.INFO)


def main():
    # Create tables if they don't exist
    Base.metadata.create_all(bind=engine)
    with get_db() as db_session:
        event_queue_repo = HitRateSummarizerEventQueueRepository(db_session)
        nba_summary_repo = NBASummaryRepository(db_session)
        mlb_summary_repo = MLBSummaryRepository(db_session)
        nba_hit_rates_repo = NBAHitRatesRepository(db_session)
        mlb_hit_rates_repo = MLBHitRatesRepository(db_session)
        nba_summarizer = NBASummarizer(nba_hit_rates_repo)
        mlb_summarizer = MLBSummarizer(mlb_hit_rates_repo)
        worker = SummarizerWorker(
            nba_summarizer=nba_summarizer,
            mlb_summarizer=mlb_summarizer,
            hit_rate_summarizer_event_queue_repository=event_queue_repo,
            nba_summary_repository=nba_summary_repo,
            mlb_summary_repository=mlb_summary_repo,
        )

        while True:
            worker.process_events(batch_size=10)
            time.sleep(10)  # Poll every 10 seconds
            logging.info("Worker cycle completed, sleeping for 10 seconds...")
            

main()