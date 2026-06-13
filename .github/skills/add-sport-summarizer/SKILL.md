---
name: add-sport-summarizer
description: 'Add a new sport summarizer to bettor_index_prop_summarizer_worker. Use when creating a new sport summary model, summary repository interface and implementation, summarizer class, worker routing, main.py wiring, and pytest coverage by following the NBA pattern.'
argument-hint: 'Provide the sport name, sport_key, and the existing files to mirror if they differ from NBA.'
user-invocable: true
---

# Add Sport Summarizer

Use this skill when extending the worker to support a new sport that should produce and persist summary records in the same style as NBA.

The current reference implementation lives in these files:
- `db/models/nba_summaries.py`
- `interfaces/nba_summary_repository_interface.py`
- `repositories/nba_summary_repository.py`
- `summarizers/nba_summarizer.py`
- `worker/summarizer_worker.py`
- `main.py`
- `tests/test_nba_summary_repository.py`
- `tests/test_nba_summarizer.py`
- `tests/test_summarizer_worker.py`

## Outcome

Produce a complete new-sport slice with:
- A summary persistence model for the new sport
- A repository interface and repository implementation for that summary model
- A summarizer class implementing `ISummarizerInterface`
- Worker routing for the new `sport_key`
- Application wiring in `main.py`
- Tests covering summary insertion and the new summarizer behavior

## Required Behavior

The new summarizer must:
- Fetch hit rates for `(event_id, market_key, outcome_description)`
- Return `None` when no hit rates exist
- Build a summary payload with market metadata
- Find line discrepancy for `over` and `under`
- Find odds discrepancy for `over` and `under`
- Identify the best over line
- Identify the best under line
- Identify the best over price
- Identify the best under price
- Persist the summary through the new sport summary repository

## Procedure

1. Confirm the naming plan.
   Use a consistent set of names before editing:
   - Model: `<Sport>Summary`
   - Repository interface: `I<Sport>SummaryRepository`
   - Repository: `<Sport>SummaryRepository`
   - Summarizer: `<Sport>Summarizer`
   - Table: `<sport>_summaries`
   - Test files: `test_<sport>_summary_repository.py`, `test_<sport>_summarizer.py`

2. Inspect the NBA reference before copying patterns.
   Read the NBA files listed above and verify:
   - The summary table schema and composite key fields
   - The repository contract uses `insert_summary`
   - The repository implementation uses `merge`, `commit`, and `rollback`
   - The summarizer builds the summary dictionary from hit-rate rows
   - The worker branches on `sport_key` and inserts the correct summary model

3. Create the new summary model.
   Add `db/models/<sport>_summaries.py`.
   Requirements:
   - Inherit from `Base`
   - Use a dedicated `__tablename__`
   - Store at least `event_id`, `market_key`, `outcome_description`, `commence_time`, `home_team`, `away_team`, `summary_data`, `sport_key`, `created_at`, and `updated_at`
   - Match the NBA composite primary key pattern unless the sport has a real schema reason not to
   - Keep `summary_data` as JSON

4. Create the summary repository interface.
   Add `interfaces/<sport>_summary_repository_interface.py`.
   Requirements:
   - Define `I<Sport>SummaryRepository`
   - Declare `insert_summary(self, summary: <Sport>Summary)`
   - Keep the interface small and aligned with the existing repository pattern

5. Create the summary repository implementation.
   Add `repositories/<sport>_summary_repository.py`.
   Requirements:
   - Implement `I<Sport>SummaryRepository`
   - Accept a DB session in the constructor
   - Use `self.DB.merge(summary)`
   - Commit on success
   - Roll back and log on failure

6. Implement the new summarizer.
   Add `summarizers/<sport>_summarizer.py`.
   Requirements:
   - Implement `ISummarizerInterface`
   - Accept a repository implementing `HitRatesRepositoryInterface`
   - Provide `summarize(event_id, market_key, outcome_description)`
   - Provide `build_summary(hit_rates, event_id, market_key, outcome_description)`
   - Reproduce the NBA decision logic for:
     - `find_line_discrepancy`
     - `find_odds_discrepancy`
     - `identify_best_over_line`
     - `identify_best_under_line`
     - `identify_best_over_price`
     - `identify_best_under_price`
   - Use the new sport's hit-rate repository or an existing shared repository implementation if one already matches the data shape

7. Extend the worker for the new sport.
   Update `worker/summarizer_worker.py`.
   Requirements:
   - Inject the new summarizer and new sport summary repository
   - Add a branch for the new `sport_key`
   - Mark queue events consumed whether the summarizer returns a summary or `None`
   - Build the correct `<Sport>Summary` model from `summary["market"]`
   - Call the new repository's `insert_summary`

8. Update application wiring.
   Update `main.py`.
   Requirements:
   - Instantiate the new sport hit-rate repository if needed
   - Instantiate the new `<Sport>SummaryRepository`
   - Instantiate the new `<Sport>Summarizer`
   - Pass the new dependencies into `SummarizerWorker`
   - Keep `Base.metadata.create_all(bind=engine)` intact so the new table is created

9. Add focused tests.
   Create or extend tests for the new sport.
   Minimum coverage:
   - `tests/test_<sport>_summary_repository.py`
     - Insert creates a row
     - Re-insert updates the existing row
   - `tests/test_<sport>_summarizer.py`
     - Summary build returns the expected sections
     - Line discrepancy is detected correctly
     - Odds discrepancy is detected correctly
     - Best over line and best under line are chosen correctly
     - Best over price and best under price are chosen correctly
   - `tests/test_summarizer_worker.py`
     - Add or extend a case proving the worker routes the new `sport_key`
     - Assert the worker consumes the queue event
     - Assert the worker inserts through the new sport summary repository

10. Validate narrowly.
   Run the smallest checks that cover the new slice first:

```bash
pytest tests/test_<sport>_summary_repository.py tests/test_<sport>_summarizer.py tests/test_summarizer_worker.py
```

   If the worker constructor changes, also run:

```bash
pytest
```

## Decision Points

- If the new sport already has a hit-rate repository implementing `HitRatesRepositoryInterface`, reuse it.
- If the new sport needs a different summary schema, keep the repository and worker contract consistent while documenting the divergence.
- If worker branching starts to grow beyond a couple of sports, note that a registry-based dispatch may be cleaner, but do not refactor unless requested.

## Completion Checklist

- New summary model exists and is imported correctly
- New repository interface exists
- New repository implementation exists
- New summarizer implements `ISummarizerInterface`
- New sport is routed in `SummarizerWorker`
- `main.py` wires the new sport dependencies
- Repository insertion tests pass
- Summarizer behavior tests pass
- Worker routing test passes

## Example Prompts

- `/add-sport-summarizer Add MLB support with sport_key baseball_mlb using NBA as the reference.`
- `/add-sport-summarizer Add NHL summaries and tests; mirror the NBA repository and worker flow.`
- `/add-sport-summarizer Add WNBA support and keep the summary payload shape aligned with NBA.`