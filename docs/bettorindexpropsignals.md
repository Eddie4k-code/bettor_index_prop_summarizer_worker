# BettorIndex Prop Signals

This document explains how `bettorindexpropsignals` is calculated today in the worker and what parts of the logic are intended to be tuned in the future.

Primary implementation:
- `services/bettor_index_prop_signals_common.py`
- `services/nba_bettor_index_prop_signals_service.py`
- `services/mlb_bettor_index_prop_signals_service.py`

## Purpose

The backend computes a signal payload so the frontend can render:
- a directional lean
- a market-readiness label
- short explanation text

The frontend should not need to recompute weighted hit rates, implied probability, or edge math on its own.

## Inputs

Each sport service passes these inputs into `build_signal_payload(...)`:
- `best_over_line`
- `best_under_line`
- `best_over_price`
- `best_under_price`
- `line_discrepancy_over`
- `window_configs`

The `window_configs` are owned by each sport service. Right now MLB and NBA both use:

```python
[
    {"key": "ten_game_hit_rate", "label": "10D", "weight": 0.5},
    {"key": "thirty_game_hit_rate", "label": "30D", "weight": 0.3},
    {"key": "sixty_game_hit_rate", "label": "60D", "weight": 0.2},
]
```

## Step-By-Step Calculation

### 1. Normalize trend windows

For each configured window:
- read the hit-rate field from the selected line payload
- keep only finite numeric values
- emit a structured trend window with `label`, `value`, and `weight`

Invalid or missing values are skipped.

### 2. Compute weighted hit rates

The weighted rate for each side is:

$$
weighted\_rate = \frac{\sum(value_i \cdot weight_i)}{\sum(weight_i\ for\ available\ windows)}
$$

Important behavior:
- missing windows do not zero out the signal
- weights are automatically renormalized across only the available windows
- if no valid windows exist for a side, that side's weighted rate is `None`

### 3. Compute recent edge

If both weighted rates exist:

$$
recent\_edge = weighted\_under\_rate - weighted\_over\_rate
$$

Interpretation:
- positive `recent_edge` means the model leans `UNDER`
- negative `recent_edge` means the model leans `OVER`
- small absolute edge means no meaningful directional lean

The current no-lean threshold is:
- `WEAK_RECENT_EDGE = 0.04`

So:
- `abs(recent_edge) < 0.04` -> `side = "NONE"`

### 4. Convert American odds to implied probability

The current best price on each side is converted using raw American odds:

For positive odds:

$$
implied\_probability = \frac{100}{odds + 100}
$$

For negative odds:

$$
implied\_probability = \frac{|odds|}{|odds| + 100}
$$

This is raw implied probability, not no-vig or fair probability.

### 5. Select the active side for price comparison

Once the directional side is chosen:
- `UNDER` uses `weighted_under_rate` and `under_implied_probability`
- `OVER` uses `weighted_over_rate` and `over_implied_probability`
- `NONE` leaves both selected values as `None`

### 6. Compute value edge

If both selected values exist:

$$
selected\_value\_edge = selected\_estimated\_rate - selected\_implied\_probability
$$

Interpretation:
- positive value edge means the backend thinks the side is underpriced
- negative value edge means the backend thinks the side is overpriced

## Strength Derivation

`strength` is not what decides the side. The side is decided first from `recent_edge`.

`strength` is derived afterward from:
- `abs(recent_edge)`
- a minimum `selected_value_edge` gate

Current thresholds:
- `none` if `abs(recent_edge) < 0.04`
- `strong` if `abs(recent_edge) >= 0.15` and `selected_value_edge` is missing or at least `0.04`
- `medium` if `abs(recent_edge) >= 0.08` and `selected_value_edge` is missing or at least `0.01`
- otherwise `weak`

Constants:
- `STRONG_RECENT_EDGE = 0.15`
- `MEDIUM_RECENT_EDGE = 0.08`
- `WEAK_RECENT_EDGE = 0.04`
- `STRONG_VALUE_EDGE = 0.04`
- `MEDIUM_VALUE_EDGE = 0.01`

## Market State

`market_state` currently comes from line disagreement only:
- `unknown` when discrepancy input is missing
- `books_agree` when discrepancy is `"No line discrepancy"`
- `books_disagree` otherwise

This is currently line-based, not a full market-efficiency model.

## Action Derivation

Current decision order:

1. `side == "NONE"` -> `pass`
2. negative `selected_value_edge` -> `pass`
3. very high juice (`selected_implied_probability >= 0.7`) -> `shop_price`
4. if `market_state == "books_disagree"`:
   - allow `bet_now` only when:
     - `strength == "strong"`, and
     - `selected_value_edge >= STRONG_VALUE_EDGE`
   - otherwise `shop_line`
5. if `selected_value_edge >= required_threshold` -> `bet_now`
6. otherwise -> `shop_price`

Required threshold for non-disagreement `bet_now`:
- default: `0.01`
- if implied probability `>= 0.65`: `0.03`
- if implied probability `>= 0.7`: the logic routes to `shop_price` before `bet_now`

Constants:
- `HIGH_JUICE_IMPLIED_PROBABILITY = 0.65`
- `VERY_HIGH_JUICE_IMPLIED_PROBABILITY = 0.7`
- `HIGH_JUICE_VALUE_EDGE = 0.03`

## Simplified Frontend Contract

The payload now includes presentation-oriented fields:

### Lean label

Derived from `side` and `strength`:
- `Strong Lean Over`
- `Lean Over`
- `Slight Lean Over`
- `Strong Lean Under`
- `Lean Under`
- `Slight Lean Under`
- `No Strong Lean`

### Market label

Derived from `action`:
- `bet_now` -> `Opportunity`
- `shop_line` or `shop_price` -> `Worth Watching`
- `pass` -> `Potential Pass`

### Reason fields

The payload also includes:
- `reason_code`
- `reason_text`

`reason_text` is backend-authored and should mention:
- over or under trend when one exists
- whether the current price looks favorable
- whether books disagree

## Current Output Shape

Important fields inside `summary_data.bettorindexpropsignals`:
- `side`
- `strength`
- `action`
- `lean_label`
- `market_label`
- `reason_code`
- `reason_text`
- `market_state`
- `weighted_over_rate`
- `weighted_under_rate`
- `recent_edge`
- `over_implied_probability`
- `under_implied_probability`
- `selected_value_edge`
- `over_trend_windows`
- `under_trend_windows`
- `expected_trend_windows`
- `available_over_trend_windows`
- `available_under_trend_windows`

## What Can Be Tuned Later

These are the main levers to improve the model without redesigning everything.

### 1. Sport-specific window configs

Can tune per sport:
- which windows exist
- the labels used
- the weights assigned

Example future changes:
- NBA uses `10D/20D/40D`
- MLB keeps `10D/30D/60D`
- weights become more recent-heavy or more stable

### 2. Recent-edge thresholds

Can tune:
- what counts as no lean
- what counts as weak, medium, and strong

These live in:
- `WEAK_RECENT_EDGE`
- `MEDIUM_RECENT_EDGE`
- `STRONG_RECENT_EDGE`

### 3. Value-edge thresholds

Can tune:
- default `bet_now` edge threshold
- high-juice threshold
- disagreement-specific `Opportunity` threshold

These live in:
- `MEDIUM_VALUE_EDGE`
- `HIGH_JUICE_VALUE_EDGE`
- `STRONG_VALUE_EDGE`

### 4. Disagreement policy

Current behavior:
- disagreement is cautionary, not automatically disqualifying
- strong disagreement cases can still become `Opportunity`

Future tuning options:
- require an even higher edge than `0.04`
- separate line disagreement from price disagreement
- downgrade only mild disagreement but allow stronger positive reasons in `reason_text`

### 5. High-juice handling

Current behavior:
- very high implied probability (`>= 0.7`) forces `shop_price`

Future tuning options:
- allow `Opportunity` for elite signals despite heavy juice
- make the high-juice rule sport-specific

### 6. Reason-text strategy

Can tune:
- how explicit the backend is about shopping behavior
- how much of the explanation is stable `reason_code` versus display text

### 7. Market-shape generalization

Current logic is over/under-shaped.

Future work may need to redesign the signal contract for:
- yes/no markets
- other two-outcome markets with non-over/under labels

### 8. Pricing model quality

Current value edge uses raw implied probability from a single best price.

Future improvements:
- de-vig fair probability
- compare across both sides more explicitly
- incorporate price disagreement directly into value assessment

## Known Limitations

1. `market_state` is based on line disagreement only, not full market quality.
2. Value edge uses raw implied probability, not no-vig probability.
3. The current contract assumes over/under style markets.
4. `is_finite_number(...)` currently treats Python booleans as numeric because `bool` is a subclass of `int`.

## Recommended Future Review Questions

When revisiting this system later, check:
- Are sport-specific windows still appropriate?
- Are the lean thresholds too aggressive or too weak?
- Is the disagreement `Opportunity` threshold too permissive or too strict?
- Should line disagreement and price disagreement be handled separately?
- Should the value-edge model move to no-vig pricing?
- Is the simplified frontend contract still sufficient for user understanding?