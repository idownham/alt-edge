# S1 extension scored once: pooled verdict STOP (2026-11-25)

**What was run:** `python scripts/score_extension.py --frozen-hash bb92f3a`, run **once** at 2026-11-25T05:52:11Z.
Raw output: `score-extension-2026-11-25.json`; once-only marker: `scored-locked.json`.

**Model and rule:**
- Model: the frozen blend-v1, commit `bb92f3a`, unchanged. The freeze guard passed and the corpus fingerprint
  matched.
- Rule: the pooling rule (`decisions.md`, 2026-11-09). The extension set was built under option B (`decisions.md`,
  2026-11-25).

**Before scoring:**
- The re-derived test Brier reproduced the recorded 0.1614 / 0.1631.
- No extension outcome had been read.

**Timing:** scoring ran on 2026-11-25. That is after the Nov 21 earliest-run date and after the Nov 22 time box,
because the Factbase redesign stopped collection and needed Ian's decision. The extension window (first close
through 2026-11-20) was fixed in advance and wasn't changed.

## Results (KXTRUMPMENTION, spec-v2 filters)
| Set | Events | Markets | Brier model | Brier market | Diff | 95% CI (event-clustered) | Log loss model / market |
|---|---|---|---|---|---|---|---|
| Test (re-derived) | 60 | 1,640 | 0.1614 | 0.1631 | −0.0017 | [−0.0043, +0.0010] | 0.4882 / 0.4918 |
| Extension alone (reported, doesn't decide) | 11 | 403 | 0.1383 | 0.1372 | +0.0011 | [−0.0039, +0.0063] | 0.4372 / 0.4313 |
| **Pooled test + extension (decides)** | **71** | **2,043** | **0.1568** | **0.1580** | **−0.0011** | **[−0.0035, +0.0012]** | 0.4782 / 0.4799 |
| Base rate alone, pooled (reported only) | 71 | 2,043 | 0.2290 | 0.1580 | +0.0711 | [+0.0573, +0.0845] | 0.6500 / 0.4799 |

The bootstrap used 10,000 draws over events, seed 20261014.

## Gate (spec v2 + pooling rule)
1. **Size floor** (≥ 300 markets / ≥ 30 events): met, 2,043 / 71.
2. **Model Brier < market:** yes on the point estimate (0.1568 vs 0.1580).
3. **Upper 95% bound < 0:** **no**. It is +0.0012.

The pooled result is INCONCLUSIVE. After the one extension only PASS or STOP is allowed, so the pooling rule makes
this **STOP: no demonstrated edge.** Ian confirms the verdict (`decisions.md`).

## Pooled results by event type (reported only; small groups)
| Type | Events | Markets | Brier model | Brier market |
|---|---|---|---|---|
| remarks | 33 | 965 | 0.1475 | 0.1495 |
| rally | 22 | 714 | 0.1565 | 0.1552 |
| bilateral | 7 | 143 | 0.2083 | 0.2100 |
| interview | 5 | 120 | 0.1737 | 0.1846 |
| address | 2 | 51 | 0.1585 | 0.1430 |
| press_conference | 2 | 50 | 0.1523 | 0.1632 |

## What this says
- The frozen blend stayed close to the market price, about 0.001 Brier better on the pooled point estimate.
- On the new events alone it was slightly worse.
- The pooled confidence interval still includes zero, so a better-calibrated forecast than the market is **not
  demonstrated**.
- Transcript base rates on their own are much worse than the market (+0.071). Most of what the blend gets right
  comes from the market price itself.

## Caveats (stated plainly)
- **Extension set (option B):** it covers 11 events / 403 markets with first close Oct 15 – Nov 8.
  - The 2 events with first close Nov 9–20 had no Factbase start time, because the calendar was redesigned (evidence
    commit `7b7ac57`).
  - 6 earlier locked events never had a matching Factbase entry. They drop out under the spec's filter, as in the
    test set.
- **Base rates:** for extension events they used transcripts through 2026-11-08. That is everything the frozen
  pipeline had, and all of it predates each event.
- **Q7 paper gate:** stays **INCOMPLETE** (`decisions.md`). With STOP it is not run.
