# alt-edge (Project Bloodhound) — Spec

*Captured 2026-10-14 in the planning chat. Status: S0 (started 2026-10-14). Criteria: v2 CONFIRMED 2026-10-14.*

## Hypothesis
Some prediction markets — starting with **mention markets** ("Will [person] say [word] during [event]?") — are
priced by casual traders on gut feel. Doing the homework (historical base rates, reading the exact rules, event
context) produces probability estimates that are better calibrated than the market's, often enough to beat fees.

## Why mention markets first
Many similar events, rich public transcripts, frequent resolutions, mostly retail traders, and rules with fine print
that many traders skip. Expand to other categories only after the method is shown to be calibrated here.

## Edge sources to test
1. **Base rates:** frequency of word X in comparable events (rally / press conference / interview / address), by
   length, topic, recency.
2. **Rule fine print:** word-form rules (plurals, compounds), who must say it, event window, sources used to
   resolve. Flag markets whose rules differ from what the title implies.
3. **Event context:** scheduled length, topic, news of the day.
4. **Live updating:** probability decay as an event runs without the word; does the market update too slowly?

## Method
- Collect markets: Kalshi mention series (and others later) — titles, rules, prices over time, outcomes.
- Collect transcripts for past events of the same speakers; build a searchable corpus honoring each market's
  word-form rules.
- Model: base-rate estimate adjusted for event type/length/context → probability. AI may read rules and propose
  adjustments, but every estimate is logged.
- **Calibration backtest (gate before any money):** on past resolved markets, does the model's 70% happen ~70% of
  the time? Is it better calibrated than the market's price (Brier/log score)? Out-of-sample only.
- Paper trade: log every market where model − price > fees + margin; track results.

## Pre-registered criteria — v2, CONFIRMED by Ian 2026-10-14
*Drafted by Claude from S0 findings (`docs/s0-research.md`). Confirmed by Ian 2026-10-14 (Q1–Q9, `docs/decisions.md`)
before any outcome data was analysed. Any change is recorded in `decisions.md`, with the reason, before it is
applied.*

**Why v1 changed:** mention markets close early once the word is said (`can_close_early`), so the last price on a
YES is about $0.99. Scoring against the "closing price" would let the market see the answer. The benchmark is moved
to a fixed pre-event time.

**Universe.** Settled `KXTRUMPMENTION` word markets (**primary**: alone decides PASS/STOP). Settled `KXVANCEMENTION`
word markets (**secondary**): scored and reported separately under the same rules, and they never change the gate
verdict. If no usable Vance transcript or start-time source is found by the freeze, Vance is dropped and noted.
Excluded from both: "Event does not qualify" strikes; events with no scheduled start time (Roll Call Factbase for
Trump; the Vance source is chosen in S1 before the freeze); markets with no two-sided quote, or a yes spread > 10¢,
at the reference time. These filters use only prices and schedules, never results, and are applied before scoring.

**Reference time and market price.** T_ref = scheduled start (ET, from the schedule source above) − 15 min. Market probability
p_mkt = midpoint of yes_bid and yes_ask from the 1-minute candlestick ending at or just before T_ref.

**Model inputs (no look-ahead).** Only transcripts with event dates before the event's date, and only information
public at T_ref. The model's code and parameters are frozen (git commit hash recorded in `decisions.md`) before the
test set is scored. AI-produced inputs are logged (prompt, model, timestamp), per `CLAUDE.md` rule 4.

**Split.** Development = events whose first market closed 2025-04-02 → 2026-05-31 (Trump 157 events / 4,114 markets,
Vance 39 / 883, before filters); used freely to build and tune. Held-out test = events 2026-06-01 → 2026-10-14
(Trump 84 / 2,744, Vance 32 / 796, before filters). **The test set is scored exactly once**, after the freeze.

**Calibration gate — KXTRUMPMENTION (PASS needs all of these):**
1. ≥ 300 test markets across ≥ 30 test events after filters.
2. Model Brier < market Brier (p_mkt) on the test set.
3. Event-clustered bootstrap (resample events, 10,000 draws, fixed seed): the 95% upper bound of
   (model Brier − market Brier) is < 0.
4. Reported but not gating: log loss, a reliability table (10 bins), and results by event type.
5. Vance secondary result: the same tests 1–3 on KXVANCEMENTION, reported as its own pass / fail / too-few-events
   result. Not part of the gate.

**Paper-trade gate** (KXTRUMPMENTION only; only after a calibration PASS; forward events listed after the
freeze, nothing re-used from the test set):
- Signal: |p_model − price| > taker fee at that price + 3¢. Buy YES at yes_ask or NO at (1 − yes_bid), from the
  1-minute candle at T_ref. **5 contracts**, held to settlement. Taker fee ceil-to-cent 0.07·C·P·(1−P), no maker fee
  (Ian checked kalshi.com/fee-schedule 2026-10-14). Money in Decimal.
- PASS: ≥ 50 paper trades across ≥ 10 events, total net P&L after fees > 0, and the edge where the model predicted
  it: sorted by predicted edge, the top half's net P&L per trade ≥ the bottom half's.
- If 2026-11-22 arrives first: report **INCOMPLETE** with the trades so far. Thresholds are not lowered; collection
  continues after the class.
- Reconstructed after the fact from public candlesticks, so no continuously running collector is needed.

**STOP (any one ends the mention-market line):**
- The test-set point estimate of model Brier ≥ market Brier.
- Fewer than 30 usable Trump test events after filters (data not feasible).
- Paper trading is net negative after fees at 50 trades.
- **Inconclusive** (model better on the point estimate, but the CI crosses 0): no re-tuning on the test set. One
  extension only: score the frozen model on new events through 2026-11-20, then PASS or STOP on all of it together.
- Time box: no calibration PASS by 2026-11-22 → write up as "no demonstrated edge" for the class.

**Live (if ever):** same cap style as Slot Machine; owner decision recorded first. Unchanged from v1.

<details><summary>v1 DRAFT (2026-10-14 planning chat), kept for the record</summary>

- Calibration: model Brier score beats the market's closing-price Brier score on ≥ 100 out-of-sample markets.
- Paper: ≥ 50 paper trades, net positive after fees, with the edge concentrated where the model predicted it.
- Live (if ever): same caps style as Slot Machine; owner decision recorded first.


</details>

## Open questions for S0 (answered 2026-10-14 in `docs/s0-research.md`)
- Which Kalshi series cover mention markets; volume and depth; fee type; how rules define word matches.
- Best free transcript sources and their coverage/latency.
- How often markets resolve; whether historical prices are available.
