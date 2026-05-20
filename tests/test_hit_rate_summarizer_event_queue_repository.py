import unittest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from db.models.base import Base
from db.models.hit_rate_summarizer_event_queue import HitRateSummarizerQueue
from interfaces.hit_rate_summarizer_event_queue_repository import IHitRateSummarizerEventQueueRepository
from repositories.hit_rate_summarizer_event_queue_repository import HitRateSummarizerEventQueueRepository

class TestHitRateSummarizerEventQueueRepository(unittest.TestCase):
    def setUp(self):
        # Use in-memory SQLite database
        self.engine = create_engine('sqlite:///:memory:')
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)
        self.db = self.Session()
        self.repo = HitRateSummarizerEventQueueRepository(self.db)

    def tearDown(self):
        self.db.close()
        self.engine.dispose()

    def test_consume_pending_event(self):
        # Insert a pending event
        event = HitRateSummarizerQueue(
            event_id='1',
            market_key='market1',
            outcome_description='desc',
            status='pending',
            sport_key='sport1'
        )
        self.db.add(event)
        self.db.commit()

        # Fetch pending events
        pending_events = self.repo.fetch_pending_events(batch_size=10)
        self.assertEqual(len(pending_events), 1)
        fetched_event = pending_events[0]
        self.assertEqual(fetched_event.status, 'pending')

        # Mark as consumed
        self.repo.mark_event_consumed(fetched_event)
        updated_event = self.db.query(HitRateSummarizerQueue).get((
            '1', 'market1', 'desc'))
        self.assertEqual(updated_event.status, 'consumed')

if __name__ == '__main__':
    unittest.main()
