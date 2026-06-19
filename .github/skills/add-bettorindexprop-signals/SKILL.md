---
name: add-bettorindexprop-signals
description: 'Add or modify bettorindexpropsignals in bettor_index_prop_summarizer_worker. Use when implementing sport-specific signal services, configuring hit-rate windows and weights, handling missing windows by renormalizing remaining weights, wiring signals into MLB or NBA summarizers, checking over-under versus yes-no market shape assumptions, and adding focused pytest coverage.'
argument-hint: 'Provide the sport, market shape, windows, weights, and any signal-threshold changes.'
user-invocable: true
---

# Add Bettor Index Prop Signals

Use this skill when implementing or changing `bettorindexpropsignals` in this worker.

The current reference implementation lives in these files:
- `interfaces/bettor_index_prop_signals_interface.py`
- `services/bettor_index_prop_signals_common.py`
- `services/mlb_bettor_index_prop_signals_service.py`
- `services/nba_bettor_index_prop_signals_service.py`
- `summarizers/mlb_summarizer.py`
- `summarizers/nba_summarizer.py`
- `main.py`
- `tests/test_bettor_index_prop_signals_service.py`
- `tests/test_mlb_summarizer.py`
- `tests/test_nba_summarizer.py`
- `tests/test_summarizer_worker.py`

## Outcome

Produce a complete signal slice that:
- Calculates a `bettorindexpropsignals` payload for the target sport
- Uses sport-owned window configuration instead of hardcoding one shared window set
- Renormalizes weights across only the windows that are actually available
- Emits JSON-safe signal fields in the summary payload
- Is wired into the relevant summarizer and application setup
- Is covered by focused tests for signal math and summarizer integration

## Required Behavior

The signal implementation must:
- Keep sport-specific signal classes separate from day one
- Accept missing hit-rate windows without failing
- Renormalize the weighted rate using only available windows
- Treat invalid numeric values as unusable inputs
- Compute implied probability from American odds consistently
- Compute value edge as estimated rate minus implied probability
- Return a stable payload even when some inputs are absent
- Be explicit about market-shape assumptions before relying on `over` and `under`

## Procedure

1. Confirm the market shape before editing.
   Determine whether the market is:
   - `over/under`
   - `yes/no`
   - another two-sided shape

   If the request is not clearly `over/under`, do not blindly reuse `best_over_*` and `best_under_*` assumptions. Call out the mismatch first.

2. Confirm the sport-specific window plan.
   For the target sport, identify:
   - which hit-rate fields exist now
   - which windows should contribute to the signal
   - what weights each window should carry

   Do not assume every sport uses `10D/30D/60D`.

3. Keep the service boundary sport-owned.
   Use or create a dedicated service such as:
   - `MLBBettorIndexPropSignalsService`
   - `NBABettorIndexPropSignalsService`

   Shared math helpers can live in `services/bettor_index_prop_signals_common.py`, but sport configuration belongs in the sport service.

4. Normalize only valid windows.
   In the common signal math:
   - include only finite numeric values
   - skip missing, `None`, `NaN`, and infinite inputs
   - compute weighted rate as:

   $$weighted\_rate = \frac{\sum(value_i \cdot weight_i)}{\sum(weight_i\ for\ available\ windows)}$$

   This must renormalize remaining weights automatically when one or more configured windows are missing.

5. Keep edge math internally consistent.
   For the current `over/under` model:
   - directional edge compares the two sides consistently
   - selected value edge equals estimated rate minus implied probability
   - side mapping must match the sign convention in the directional edge

   If you change subtraction order, also change the sign interpretation and tests.

6. Wire signals into the summarizer, not the worker.
   The summarizer should:
   - build the usual market, line, and odds sections
   - call the sport-specific signal service
   - append `summary["bettorindexpropsignals"]`

   The worker should persist `summary_data` unchanged.

7. Keep payloads JSON-safe.
   Any datetime-like values included in the summary or related sections must be serialized before persistence.
   The signal payload itself should stay primitive: strings, floats, booleans, lists, and dicts.

8. Add focused tests before broad validation.
   Minimum coverage:
   - direct signal-service math test
   - missing-window renormalization test
   - sport-specific window-configuration test
   - summarizer test asserting `bettorindexpropsignals` is present
   - worker test proving the signal payload persists through `summary_data`

9. Validate narrowly first.
   Run the smallest useful slice before widening scope:

```bash
pytest tests/test_bettor_index_prop_signals_service.py tests/test_nba_summarizer.py tests/test_mlb_summarizer.py tests/test_summarizer_worker.py
```

10. Expand only if the first validation passes.
   If the signal math test fails:
   - fix the math or the test expectation
   - rerun the same focused test first

   If the summarizer tests fail:
   - inspect the local payload shape and service wiring
   - rerun only the touched summarizer tests before broader checks

## Decision Points

- If a sport uses different windows, configure them in that sport's signal service rather than changing another sport's defaults.
- If a configured window is missing in a hit-rate row, renormalize with the remaining windows rather than treating the whole signal as invalid.
- If all configured windows are missing for a side, return `None` for that weighted rate and fall back to a neutral signal outcome.
- If the market is truly `yes/no`, treat the current `over/under` implementation as a structural mismatch and redesign the signal boundary before extending it.
- If the user asks for fair-probability or no-vig edge, do not claim the current implied-probability math already does that. Add a separate calculation intentionally.

## Completion Checklist

- A sport-specific signal service exists for the target sport
- Window config lives in the sport service, not in a global hardcoded constant
- Missing windows renormalize remaining weights correctly
- Invalid numeric values are ignored safely
- `bettorindexpropsignals` is attached in the summarizer payload
- `main.py` wires the signal service into the target summarizer
- Focused signal-service tests pass
- Focused summarizer tests pass
- Worker persistence test passes

## Example Prompts

- `/add-bettorindexprop-signals Add bettorindexpropsignals for MLB using 10D, 30D, and 60D windows with renormalization when 60D is missing.`
- `/add-bettorindexprop-signals Update NBA signals to use 10D and 30D only, keeping the signal payload shape unchanged.`
- `/add-bettorindexprop-signals Add a new sport-specific signal service and wire it into the summarizer and tests.`
- `/add-bettorindexprop-signals Evaluate whether a yes-no market can reuse the current signal model or needs a market-shape refactor.`