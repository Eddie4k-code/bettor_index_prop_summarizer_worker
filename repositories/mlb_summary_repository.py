import json
import logging
from datetime import datetime

from db.models.mlb_summaries import MLBSummary
from interfaces.mlb_summary_repository_interface import IMLBSummaryRepository


logger = logging.getLogger(__name__)


def _debug_json_serializable(value):
    try:
        json.dumps(value)
        return True
    except TypeError:
        return False


class MLBSummaryRepository(IMLBSummaryRepository):
    def __init__(self, DB):
        self.DB = DB

    def insert_summary(self, summary: MLBSummary):
        """
        Insert or update an MLB summary in the database.
        Args:
            summary: MLBSummary instance.
        """
        try:
            # #region agent log
            _ha = (summary.summary_data or {}).get("home_away_last_n_clears")
            try:
                with open("/Users/eddieoconnor/Documents/projects/betting_agent/bettor_index_prop_summarizer_worker/.cursor/debug-4c1736.log", "a") as _f:
                    _f.write(json.dumps({"sessionId": "4c1736", "hypothesisId": "C", "location": "mlb_summary_repository.py:insert_summary", "message": "summary_data home_away_last_n_clears at insert", "data": {"type": type(_ha).__name__ if _ha is not None else None, "json_ok": _debug_json_serializable(summary.summary_data)}, "timestamp": int(datetime.now().timestamp() * 1000)}) + "\n")
            except Exception:
                pass
            # #endregion
            self.DB.merge(summary)
            self.DB.commit()
        except Exception as e:
            logger.error(f"Error inserting MLB summary: {e}")
            self.DB.rollback()