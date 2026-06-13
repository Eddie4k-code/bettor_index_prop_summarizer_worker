import pytest
from worker.summarizer_worker import SummarizerWorker

class FakeEvent:
    def __init__(self, event_id, market_key, outcome_description, sport_key="basketball_nba"):
        self.event_id = event_id
        self.market_key = market_key
        self.outcome_description = outcome_description
        self.sport_key = sport_key

def test_summarizer_worker_processes_events(mocker):
    fake_events = [
        FakeEvent("evt1", "points", "over", "basketball_nba"),
        FakeEvent("evt2", "player_hits", "Aaron Judge", "baseball_mlb"),
    ]
    fake_summaries = [
        {"market": {"event_id": "evt1", "market_key": "points", "outcome_description": "over", "commence_time": None, "home_team": "A", "away_team": "B", "sport_key": "basketball_nba"}},
        {"market": {"event_id": "evt2", "market_key": "player_hits", "outcome_description": "Aaron Judge", "commence_time": None, "home_team": "A", "away_team": "B", "sport_key": "baseball_mlb"}}
    ]

    mock_queue_repo = mocker.Mock()
    mock_queue_repo.fetch_pending_events.return_value = fake_events
    mock_queue_repo.mark_event_consumed = mocker.Mock()

    mock_summarizer = mocker.Mock()
    mock_summarizer.summarize.return_value = fake_summaries[0]
    mock_mlb_summarizer = mocker.Mock()
    mock_mlb_summarizer.summarize.return_value = fake_summaries[1]

    mock_nba_summary_repo = mocker.Mock()
    mock_nba_summary_repo.insert_summary = mocker.Mock()
    mock_mlb_summary_repo = mocker.Mock()
    mock_mlb_summary_repo.insert_summary = mocker.Mock()

    worker = SummarizerWorker(
        nba_summarizer=mock_summarizer,
        mlb_summarizer=mock_mlb_summarizer,
        hit_rate_summarizer_event_queue_repository=mock_queue_repo,
        nba_summary_repository=mock_nba_summary_repo,
        mlb_summary_repository=mock_mlb_summary_repo,
    )

    worker.process_events(batch_size=2)


    assert mock_queue_repo.mark_event_consumed.call_count == 2
    assert mock_nba_summary_repo.insert_summary.call_count == 1
    assert mock_mlb_summary_repo.insert_summary.call_count == 1
    mock_summarizer.summarize.assert_called_once_with("evt1", "points", "over")
    mock_mlb_summarizer.summarize.assert_called_once_with("evt2", "player_hits", "Aaron Judge")


def test_summarizer_worker_consumes_mlb_event_when_no_summary(mocker):
    fake_event = FakeEvent("evt3", "player_hits", "Juan Soto", "baseball_mlb")

    mock_queue_repo = mocker.Mock()
    mock_queue_repo.fetch_pending_events.return_value = [fake_event]
    mock_queue_repo.mark_event_consumed = mocker.Mock()

    mock_nba_summarizer = mocker.Mock()
    mock_mlb_summarizer = mocker.Mock()
    mock_mlb_summarizer.summarize.return_value = None
    mock_nba_summary_repo = mocker.Mock()
    mock_mlb_summary_repo = mocker.Mock()

    worker = SummarizerWorker(
        nba_summarizer=mock_nba_summarizer,
        mlb_summarizer=mock_mlb_summarizer,
        hit_rate_summarizer_event_queue_repository=mock_queue_repo,
        nba_summary_repository=mock_nba_summary_repo,
        mlb_summary_repository=mock_mlb_summary_repo,
    )

    worker.process_events(batch_size=1)

    mock_queue_repo.mark_event_consumed.assert_called_once_with(fake_event)
    mock_mlb_summary_repo.insert_summary.assert_not_called()
