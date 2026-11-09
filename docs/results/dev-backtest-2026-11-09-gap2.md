# Dev backtest — base-rate model v1 (generated 2026-11-09T16:32:40Z)

Dev period only (events whose first market closed ≤ 2026-05-31). **No test or locked outcomes were read.**
Corpus: 1008 Factbase transcripts with Trump speech. Look-ahead rule: transcript date ≤ event ET date − 2 day(s).

Dev after spec-v2 filters: 114 events / 2583 markets. Split by event start: dev-A = first 57 events / 1145 markets (2025-04-02 → 2025-11-21); dev-B = last 57 events / 1438 markets (2025-11-24 → 2026-05-27).
Parameters are chosen on dev-A only; dev-B is the out-of-sample check.

## Grid (dev-A Brier, 270 combinations, top 15)

| Brier A | pool | last N | min secs | prior s | prior m |
|---|---|---|---|---|---|
| 0.2298 | all | 5 | 900 | 8.0 | 0.487 |
| 0.2299 | all | 10 | 900 | 16.0 | 0.487 |
| 0.2306 | all | 20 | 900 | 16.0 | 0.487 |
| 0.2309 | same_type_fallback | 10 | 900 | 16.0 | 0.487 |
| 0.2314 | all | 10 | 900 | 8.0 | 0.487 |
| 0.2318 | same_type | 10 | 900 | 16.0 | 0.487 |
| 0.2324 | all | 5 | 900 | 4.0 | 0.487 |
| 0.2326 | same_type_fallback | 5 | 900 | 8.0 | 0.487 |
| 0.2327 | same_type_fallback | 10 | 900 | 8.0 | 0.487 |
| 0.2330 | same_type | 10 | 900 | 8.0 | 0.487 |
| 0.2332 | all | 5 | 900 | 16.0 | 0.487 |
| 0.2334 | same_type | 5 | 900 | 8.0 | 0.487 |
| 0.2334 | same_type_fallback | 20 | 900 | 16.0 | 0.487 |
| 0.2343 | same_type | 20 | 900 | 16.0 | 0.487 |
| 0.2347 | same_type_fallback | 5 | 900 | 16.0 | 0.487 |

Blend (logistic, fit on dev-A): z = -0.083 + 1.145·logit(p_mkt) + 0.461·logit(p_base)

## Results (Brier: lower is better; diff = model − market, 95% event-clustered bootstrap)

| Model, sample | events | markets | Brier model | Brier market | diff | 95% CI | log loss model | log loss market |
|---|---|---|---|---|---|---|---|---|
| base, dev-A | 57 | 1145 | 0.2298 | 0.1697 | +0.0601 | [+0.0443, +0.0763] | 0.6517 | 0.5092 |
| base, dev-B | 57 | 1438 | 0.2342 | 0.1609 | +0.0733 | [+0.0578, +0.0888] | 0.6609 | 0.4872 |
| blend, dev-A | 57 | 1145 | 0.1655 | 0.1697 | -0.0041 | [-0.0084, +0.0003] | 0.4985 | 0.5092 |
| blend, dev-B | 57 | 1438 | 0.1621 | 0.1609 | +0.0012 | [-0.0015, +0.0040] | 0.4893 | 0.4872 |

### Reliability, base, dev-B (model | market)

| bin | n model | mean p | freq | n market | mean p | freq |
|---|---|---|---|---|---|---|
| 0.0-0.1 | 0 | 0.000 | 0.000 | 152 | 0.057 | 0.013 |
| 0.1-0.2 | 0 | 0.000 | 0.000 | 216 | 0.148 | 0.148 |
| 0.2-0.3 | 391 | 0.300 | 0.271 | 165 | 0.251 | 0.242 |
| 0.3-0.4 | 255 | 0.377 | 0.416 | 168 | 0.350 | 0.345 |
| 0.4-0.5 | 260 | 0.454 | 0.473 | 117 | 0.444 | 0.436 |
| 0.5-0.6 | 233 | 0.531 | 0.571 | 107 | 0.551 | 0.514 |
| 0.6-0.7 | 299 | 0.636 | 0.589 | 123 | 0.644 | 0.642 |
| 0.7-0.8 | 0 | 0.000 | 0.000 | 130 | 0.748 | 0.762 |
| 0.8-0.9 | 0 | 0.000 | 0.000 | 165 | 0.846 | 0.836 |
| 0.9-1.0 | 0 | 0.000 | 0.000 | 95 | 0.933 | 0.947 |

### Reliability, blend, dev-B (model | market)

| bin | n model | mean p | freq | n market | mean p | freq |
|---|---|---|---|---|---|---|
| 0.0-0.1 | 278 | 0.051 | 0.047 | 152 | 0.057 | 0.013 |
| 0.1-0.2 | 200 | 0.145 | 0.225 | 216 | 0.148 | 0.148 |
| 0.2-0.3 | 161 | 0.246 | 0.323 | 165 | 0.251 | 0.242 |
| 0.3-0.4 | 117 | 0.351 | 0.376 | 168 | 0.350 | 0.345 |
| 0.4-0.5 | 93 | 0.449 | 0.505 | 117 | 0.444 | 0.436 |
| 0.5-0.6 | 101 | 0.550 | 0.505 | 107 | 0.551 | 0.514 |
| 0.6-0.7 | 97 | 0.649 | 0.649 | 123 | 0.644 | 0.642 |
| 0.7-0.8 | 134 | 0.757 | 0.791 | 130 | 0.748 | 0.762 |
| 0.8-0.9 | 122 | 0.853 | 0.828 | 165 | 0.846 | 0.836 |
| 0.9-1.0 | 135 | 0.938 | 0.904 | 95 | 0.933 | 0.947 |

### By event type, dev-B, base

| type | events | markets | Brier model | Brier market |
|---|---|---|---|---|
| address | 4 | 124 | 0.2306 | 0.1755 |
| bilateral | 7 | 148 | 0.2434 | 0.1597 |
| interview | 2 | 49 | 0.2235 | 0.1506 |
| press_conference | 4 | 118 | 0.2380 | 0.1762 |
| remarks | 40 | 999 | 0.2334 | 0.1580 |

### By event type, dev-B, blend

| type | events | markets | Brier model | Brier market |
|---|---|---|---|---|
| address | 4 | 124 | 0.1824 | 0.1755 |
| bilateral | 7 | 148 | 0.1595 | 0.1597 |
| interview | 2 | 49 | 0.1522 | 0.1506 |
| press_conference | 4 | 118 | 0.1776 | 0.1762 |
| remarks | 40 | 999 | 0.1586 | 0.1580 |

Candidate base-model parameters (prior mean re-estimated on all dev): `{"pool": "all", "last_n": 5, "min_seconds": 900, "prior_strength": 8.0, "prior_mean": 0.4653503677893922, "gap_days": 2}`
