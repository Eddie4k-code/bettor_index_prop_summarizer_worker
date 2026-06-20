import time
from db.db import get_db
from repositories.game_repository import GameRepository
from repositories.hit_rate_summarizer_event_queue_repository import HitRateSummarizerEventQueueRepository
from repositories.mlb_hit_rate_repository import MLBHitRatesRepository
from repositories.mlb_player_injuries_repository import MLBPlayerInjuriesRepository
from repositories.mlb_player_stats_repository import MLBPlayerStatsRepository
from repositories.mlb_summary_repository import MLBSummaryRepository
from repositories.nba_hit_rate_repository import NBAHitRatesRepository
from repositories.nba_player_stats_repository import NBAPlayerStatsRepository
from repositories.nba_summary_repository import NBASummaryRepository
from services.mlb_bettor_index_prop_signals_service import MLBBettorIndexPropSignalsService
from services.mlb_relevant_injury_context_service import MLBRelevantInjuryContextService
from services.mlb_venue_last_five_clears_service import MLBVenueLastFiveClearsService
from services.nba_bettor_index_prop_signals_service import NBABettorIndexPropSignalsService
from services.nba_venue_last_five_clears_service import NBAVenueLastFiveClearsService
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
        nba_player_stats_repo = NBAPlayerStatsRepository(db_session)
        mlb_player_stats_repo = MLBPlayerStatsRepository(db_session)
        game_repo = GameRepository(db_session)
        mlb_player_injuries_repo = MLBPlayerInjuriesRepository(db_session)
        nba_bettor_index_prop_signals_service = NBABettorIndexPropSignalsService()
        mlb_bettor_index_prop_signals_service = MLBBettorIndexPropSignalsService()
        nba_venue_last_five_clears_service = NBAVenueLastFiveClearsService(nba_player_stats_repo, game_repo)
        mlb_venue_last_five_clears_service = MLBVenueLastFiveClearsService(mlb_player_stats_repo, game_repo)
        mlb_relevant_injury_context_service = MLBRelevantInjuryContextService(mlb_player_injuries_repo)
        nba_summarizer = NBASummarizer(
            nba_hit_rates_repo,
            nba_bettor_index_prop_signals_service,
            nba_venue_last_five_clears_service,
        )
        mlb_summarizer = MLBSummarizer(
            mlb_hit_rates_repo,
            mlb_relevant_injury_context_service,
            mlb_bettor_index_prop_signals_service,
            mlb_venue_last_five_clears_service,
        )
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