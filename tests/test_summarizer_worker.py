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
        FakeEvent("evt2", "rebounds", "under", "basketball_nba"),
    ]
    fake_summaries = [
        {"market": {"event_id": "evt1", "market_key": "points", "outcome_description": "over", "commence_time": None, "home_team": "A", "away_team": "B", "sport_key": "basketball_nba"}},
        {"market": {"event_id": "evt2", "market_key": "rebounds", "outcome_description": "under", "commence_time": None, "home_team": "A", "away_team": "B", "sport_key": "basketball_nba"}}
    ]

    mock_queue_repo = mocker.Mock()
    mock_queue_repo.fetch_pending_events.return_value = fake_events
    mock_queue_repo.mark_event_consumed = mocker.Mock()

    mock_summarizer = mocker.Mock()
    mock_summarizer.summarize.side_effect = fake_summaries

    mock_nba_summary_repo = mocker.Mock()
    mock_nba_summary_repo.insert_summary = mocker.Mock()

    # Adjust SummarizerWorker to accept nba_summary_repository if needed
    worker = SummarizerWorker(
        nba_summarizer=mock_summarizer,
        hit_rate_summarizer_event_queue_repository=mock_queue_repo,
        nba_summary_repository=mock_nba_summary_repo
    )

    worker.process_events(batch_size=2)


    assert mock_queue_repo.mark_event_consumed.call_count == 2
    assert mock_nba_summary_repo.insert_summary.call_count == 2
    mock_summarizer.summarize.assert_any_call("evt1", "points", "over")
    mock_summarizer.summarize.assert_any_call("evt2", "rebounds", "under")
