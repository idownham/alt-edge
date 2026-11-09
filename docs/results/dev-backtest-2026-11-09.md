# Dev backtest — base-rate model v1 (generated 2026-11-09T16:32:34Z)

Dev period only (events whose first market closed ≤ 2026-05-31). **No test or locked outcomes were read.**
Corpus: 1008 Factbase transcripts with Trump speech. Look-ahead rule: transcript date ≤ event ET date − 1 day(s).

Dev after spec-v2 filters: 114 events / 2583 markets. Split by event start: dev-A = first 57 events / 1145 markets (2025-04-02 → 2025-11-21); dev-B = last 57 events / 1438 markets (2025-11-24 → 2026-05-27).
Parameters are chosen on dev-A only; dev-B is the out-of-sample check.

## Grid (dev-A Brier, 270 combinations, top 15)

| Brier A | pool | last N | min secs | prior s | prior m |
|---|---|---|---|---|---|
| 0.2296 | all | 5 | 900 | 8.0 | 0.487 |
| 0.2297 | all | 10 | 900 | 16.0 | 0.487 |
| 0.2305 | all | 20 | 900 | 16.0 | 0.487 |
| 0.2309 | all | 10 | 900 | 8.0 | 0.487 |
| 0.2311 | same_type_fallback | 10 | 900 | 16.0 | 0.487 |
| 0.2319 | same_type | 10 | 900 | 16.0 | 0.487 |
| 0.2319 | all | 5 | 900 | 4.0 | 0.487 |
| 0.2330 | same_type_fallback | 10 | 900 | 8.0 | 0.487 |
| 0.2330 | same_type_fallback | 5 | 900 | 8.0 | 0.487 |
| 0.2331 | all | 10 | 300 | 16.0 | 0.487 |
| 0.2331 | same_type | 10 | 900 | 8.0 | 0.487 |
| 0.2332 | all | 5 | 900 | 16.0 | 0.487 |
| 0.2336 | same_type_fallback | 20 | 900 | 16.0 | 0.487 |
| 0.2336 | same_type | 5 | 900 | 8.0 | 0.487 |
| 0.2338 | all | 5 | 300 | 8.0 | 0.487 |

Blend (logistic, fit on dev-A): z = -0.086 + 1.145·logit(p_mkt) + 0.451·logit(p_base)

## Results (Brier: lower is better; diff = model − market, 95% event-clustered bootstrap)

| Model, sample | events | markets | Brier model | Brier market | diff | 95% CI | log loss model | log loss market |
|---|---|---|---|---|---|---|---|---|
| base, dev-A | 57 | 1145 | 0.2296 | 0.1697 | +0.0599 | [+0.0443, +0.0760] | 0.6513 | 0.5092 |
| base, dev-B | 57 | 1438 | 0.2302 | 0.1609 | +0.0693 | [+0.0535, +0.0848] | 0.6525 | 0.4872 |
| blend, dev-A | 57 | 1145 | 0.1657 | 0.1697 | -0.0040 | [-0.0082, +0.0002] | 0.4987 | 0.5092 |
| blend, dev-B | 57 | 1438 | 0.1614 | 0.1609 | +0.0004 | [-0.0021, +0.0031] | 0.4872 | 0.4872 |

### Reliability, base, dev-B (model | market)

| bin | n model | mean p | freq | n market | mean p | freq |
|---|---|---|---|---|---|---|
| 0.0-0.1 | 0 | 0.000 | 0.000 | 152 | 0.057 | 0.013 |
| 0.1-0.2 | 0 | 0.000 | 0.000 | 216 | 0.148 | 0.148 |
| 0.2-0.3 | 374 | 0.300 | 0.254 | 165 | 0.251 | 0.242 |
| 0.3-0.4 | 271 | 0.377 | 0.402 | 168 | 0.350 | 0.345 |
| 0.4-0.5 | 254 | 0.454 | 0.465 | 117 | 0.444 | 0.436 |
| 0.5-0.6 | 223 | 0.531 | 0.574 | 107 | 0.551 | 0.514 |
| 0.6-0.7 | 316 | 0.633 | 0.614 | 123 | 0.644 | 0.642 |
| 0.7-0.8 | 0 | 0.000 | 0.000 | 130 | 0.748 | 0.762 |
| 0.8-0.9 | 0 | 0.000 | 0.000 | 165 | 0.846 | 0.836 |
| 0.9-1.0 | 0 | 0.000 | 0.000 | 95 | 0.933 | 0.947 |

### Reliability, blend, dev-B (model | market)

| bin | n model | mean p | freq | n market | mean p | freq |
|---|---|---|---|---|---|---|
| 0.0-0.1 | 277 | 0.051 | 0.043 | 152 | 0.057 | 0.013 |
| 0.1-0.2 | 199 | 0.144 | 0.231 | 216 | 0.148 | 0.148 |
| 0.2-0.3 | 160 | 0.247 | 0.300 | 165 | 0.251 | 0.242 |
| 0.3-0.4 | 122 | 0.350 | 0.393 | 168 | 0.350 | 0.345 |
| 0.4-0.5 | 101 | 0.453 | 0.515 | 117 | 0.444 | 0.436 |
| 0.5-0.6 | 90 | 0.552 | 0.522 | 107 | 0.551 | 0.514 |
| 0.6-0.7 | 101 | 0.650 | 0.634 | 123 | 0.644 | 0.642 |
| 0.7-0.8 | 122 | 0.757 | 0.779 | 130 | 0.748 | 0.762 |
| 0.8-0.9 | 129 | 0.850 | 0.853 | 165 | 0.846 | 0.836 |
| 0.9-1.0 | 137 | 0.939 | 0.891 | 95 | 0.933 | 0.947 |

### By event type, dev-B, base

| type | events | markets | Brier model | Brier market |
|---|---|---|---|---|
| address | 4 | 124 | 0.2280 | 0.1755 |
| bilateral | 7 | 148 | 0.2369 | 0.1597 |
| interview | 2 | 49 | 0.2235 | 0.1506 |
| press_conference | 4 | 118 | 0.2360 | 0.1762 |
| remarks | 40 | 999 | 0.2291 | 0.1580 |

### By event type, dev-B, blend

| type | events | markets | Brier model | Brier market |
|---|---|---|---|---|
| address | 4 | 124 | 0.1815 | 0.1755 |
| bilateral | 7 | 148 | 0.1575 | 0.1597 |
| interview | 2 | 49 | 0.1523 | 0.1506 |
| press_conference | 4 | 118 | 0.1772 | 0.1762 |
| remarks | 40 | 999 | 0.1580 | 0.1580 |

Candidate base-model parameters (prior mean re-estimated on all dev): `{"pool": "all", "last_n": 5, "min_seconds": 900, "prior_strength": 8.0, "prior_mean": 0.4653503677893922, "gap_days": 1}`
