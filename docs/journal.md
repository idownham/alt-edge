# Journal (alt-edge / Project Bloodhound)

Dated entries: work, evidence, observation, decision, AI use + Ian's judgment.

---

## 2026-10-14 — Idea captured (planning chat)

**Work:** Ian proposed finding edges across markets, starting with mention markets. Planning chat (Claude) drafted the spec (edge sources, calibration gate, draft criteria) and repo rules.

**Why it differs from the other projects:** Osprey and Slot Machine compete on speed with bots; Slot Machine's S1 backtest (12,690 windows) found no edge for A–D. Bloodhound's edge, if any, comes from research and rule-reading instead.

**AI use + Ian's judgment:** Claude recommended starting with one category (mention markets) instead of "all markets", and deferring the build until a slot opens; Ian chose the name and repo and approved planning now.

---

## 2026-10-14 — S0 started early: research done, criteria v2 proposed

**Decision (Ian, recorded first):** start S0 today, ahead of the planned trigger, to have dated evidence for the
Oct 25 checkpoint. Limit: read-only research, no continuously running collectors until a slot opens
(`decisions.md`, commit a04f46f).

**Work (Claude Code session, Ian's prompt):**
- About 60 unauthenticated, paced (≤ 1 req/s, no 429s) Kalshi public API reads, 2026-10-14 23:28–23:33 UTC. Read the
  MENTION / TRUMPSAY contract-terms PDFs, Kalshi's historical-data docs, Roll Call Factbase calendar + transcript
  pages, and Fed presser transcripts.
- Wrote `docs/s0-research.md`, evidence in `docs/evidence/s0-2026-10-14/`, the fetch helper `scripts/s0_kget.py`,
  proposed criteria v2 in `docs/spec.md` (v1 kept), and `docs/s1-plan.md` (smallest S1 build, timeline, Q1–Q9).
  Commits: a04f46f (start decision), plus the S0 research commit that follows this entry.

**Observations (dated evidence, all 2026-10-14):**
- 459 series in the Mentions category, all `quadratic` fees ×1. KXTRUMPMENTION is by far the deepest: 6,858 resolved
  markets / 241 events since 2025-04-02, about 16 events/month in 2026, median about 15k contracts traded per market.
- Old markets keep rules, results, 1-minute bid/ask candles and trades on public endpoints (`/historical/*`, cutoff
  2026-08-15). The API has no event start time.
- Rules: plurals and possessives count, other inflections don't; open and hyphenated compounds count, closed compounds
  don't; slash strikes; who counts varies (office-holder, named OR-lists, earnings-call operator). KXTRUMPSAY also
  counts Truth Social posts.
- Factbase: same-day Trump transcripts with speaker labels and timestamps, plus a schedule with start times. No terms
  page found. robots.txt blocks AI-training crawlers (question for Ian).
- Fed presser transcripts post about 8 days after the meeting.

**⭐ Evidence → decision → consequence (flag for the class):**
- *Evidence:* every mention market has `can_close_early: true` ("close and expire early if the event occurs"). E.g.
  KXTRUMPMENTION-26OCT14-TSMC's last price was $0.99 when it closed, minutes after the word was said.
- *Proposed decision (pending Ian):* drop the v1 benchmark "market's closing price". Score against the price at a
  fixed time before the scheduled start (Factbase start − 15 min), and count events (≥ 30), not just markets.
- *Consequence:* without this, the gate would compare our model to a price that already knows the answer. The market
  would look nearly perfect and any model would "fail", for the wrong reason. It also adds a dependency: S1 needs
  Factbase's schedule to get start times.

**Not done / limits:** no outcome data analysed (no YES rates or Brier scores, by design). The fee coefficient was
not re-checked against Kalshi's PDF (HTTP 429); it relies on Osprey's 2026-10-13 check. The order-book depth claim
comes from one snapshot. The White House transcript-removal claim is second-hand. Criteria v2 are **not confirmed**.

**AI use + Ian's judgment:**
- Prompt excerpts (Ian): "I'm choosing to start S0 early, today, so Bloodhound has dated evidence for the class's
  Oct 25 checkpoint"; "citing a doc page or a live public API response with its date for every claim"; "Don't mark
  anything confirmed until I approve it, and don't analyse any outcome data before I do"; "A well-evidenced 'this
  isn't feasible' is a valid S0 outcome."
- Claude (Opus 5.5) did the API reads, read the rules, and drafted the research, criteria v2, S1 plan and this entry.
  Claude chose to save only short rule excerpts plus a link, not the full Kalshi contract text, since the documents are
  copyrighted.
- Claude's own suggestions that Ian still has to judge: benchmark at start − 15 min, the ≥ 30 events floor, the
  event-clustered bootstrap, KXTRUMPMENTION-only scope, and the dev/test split date. **Ian's verdict:** pending
  (Q1–Q9 in `docs/s1-plan.md`); record accepted / revised / rejected here when decided.

---

## 2026-10-14 (later) — Criteria v2 confirmed: Ian's answers to Q1–Q9

**Work:** Ian went through Q1–Q9 (`docs/s1-plan.md`) one at a time in the same Claude Code session ("Let's go through
Q1–Q9 … one at a time so I can approve or revise the v2 criteria"). The answers were recorded in `decisions.md`
**before any outcome data was looked at**. `spec.md` is marked CONFIRMED, the S1 plan is updated, and the stage line
in `CLAUDE.md` is updated.

**AI use + Ian's judgment** (Claude offered a recommended option for each; Ian picked):
- **Accepted:** Q1 benchmark at scheduled start − 15 min; Q2 spread ≤ 10¢; Q4 Factbase allowed with limits (≤ 1
  page / 2 s, cached locally, not redistributed or used for training); Q5 test set from 2026-06-01; Q6 95% clustered
  bootstrap bound; Q7 top half ≥ bottom half, and INCOMPLETE if the deadline hits rather than lowering the bar.
- **Revised:** Q3. Claude recommended Trump only; Ian chose **Trump and Vance**, and asked to add exploring more
  mention series to the plan. In a follow-up question (Q3a), Ian accepted Claude's suggestion that Trump alone decides
  PASS/STOP, that Vance is reported separately, and that Vance is dropped (and noted) if no source is found. Claude
  pointed out the Vance test set is small (32 events before filters), so its own result may end up "too few events".
- **Changed from Claude's first draft:** Q8 paper size is 5 contracts, not the 10 first proposed (Claude re-recommended
  5 after the thin top-of-book snapshot).
- **Ian's own check:** Q9. Ian checked kalshi.com/fee-schedule in a browser: taker 0.07·C·P·(1−P), no maker fee on
  `quadratic` series. That closes the gap left when the PDF blocked automated download.

**⭐ Evidence → decision → consequence:** the S0 finding (markets close early, so the closing price contains the
answer) → Ian confirmed the pre-event benchmark (Q1) → the gate now compares against a price from before the event,
and S1 has to build a schedule-to-event mapping (Factbase start times) as a required step.

---

## 2026-11-09 — S1 started; Milestone 1 (pipeline, matcher, scoring code) done, counts only

**Decision first (Ian, recorded before any build):** S1 started on Ian's go (asked 2026-11-08). Claude showed a short
M1 plan because the old S1 dates (Oct 25 / Nov 8) had passed; Ian replied "Approve, start M1". New dates, the locking of
post-Oct-14 events, and keyword event types are recorded in `decisions.md` (2026-11-09). The criteria are unchanged.

**Work (Claude Code session started from the HQ session; commits 1e68991, 17c23e6 and the wrap-up commit after this):**
- Package `src/bloodhound/` with the `bloodhound` command: `collect-markets`, `collect-schedule`, `map-events`,
  `collect-prices`, `collect-transcripts`, `status`. Stdlib only, SQLite in `data/` (gitignored).
- All network work was hand-run, one-off, paced batches from the laptop, with no keys and no orders. Kalshi public API
  ≤ 1 req/s with a 10 s back-off on 429 (about 5,330 requests in total, 0 × 429). Factbase ≤ 1 page / 2 s, each page
  fetched once (35 calendar pages + 1,252 transcript pages; only extracted segments are cached, 36 MB). Nothing runs
  continuously.
- Outcomes are stored in their own table. `db.outcomes()` returns dev outcomes only; test and locked outcomes need
  `--score-test` plus the frozen hash on a clean HEAD. This is covered by tests.
- Word matcher with **every example from Kalshi's MENTION.pdf** (re-fetched 2026-11-09) as a test: 36 "counts" and
  16 "does not count" pass. 5 examples that depend on pronunciation (NASA spoken as a word, "Mandani", Zelenskiy,
  "firestation.com", "moneyyy") are strict xfails, because a text transcript can't decide them.
- Scoring code (Decimal midpoint, quote filter, Decimal taker fee rounded up to the cent, Brier, log loss, 10-bin
  reliability, event-clustered bootstrap with a fixed seed). It is tested on synthetic data only and **has not been run
  on any outcomes**. 96 tests pass + 5 xfail.

**Observations (dated evidence, 2026-11-09; `docs/evidence/s1-2026-11-09/`):**
- Settled word markets: KXTRUMPMENTION 7,417 and KXVANCEMENTION 1,965 (yes/no results). 44 Trump markets settled
  `scalar` (not yes/no) are left out. S0's counts differ a little (dev 157 events / 4,114 markets in S0 vs 156 / 4,070
  now; test 84 / 2,744 vs 84 / 2,615). The likely causes are scalar markets and 57 tickers that appear in both
  endpoints. The split is the same whether close dates are read in UTC or ET.
- Kalshi's historical cutoff moved to 2026-09-10 (it was 2026-08-15 in S0). The batch candle endpoint allows at most
  10,000 candles per request (HTTP 400 above that), and 1-minute candles are sparse (minutes with no change are
  missing). The candle used is the last one at or before T_ref. Its age is a median of 0 min, p90 3 min, p99 39 min,
  max 280 min (30 of 5,146 are older than 60 min). There is no staleness filter, because none is pre-registered.
- **Factbase tags are loose:** campaign rallies appear only as "Pool Report" entries, at their scheduled time. For
  example, the Bullhead City rally is listed at 4:00 PM ET while the President landed at 4:04 PM (2026-10-14). The
  matcher therefore uses event entries under any tag and drops movement/logistics entries (arrives, departs, lid,
  call time). **Dev-only check:** in 0 of 120 matched dev events did any market close before T_ref or before the
  scheduled start. The Factbase calendar starts 2025-01-18, so there is no 2024 history from the calendar.
- **Universe after the spec-v2 filters (counts only, no outcomes):**

  | KXTRUMPMENTION | events / markets before filters | word markets | scheduled start found | two-sided at T_ref | spread ≤ 10¢ |
  |---|---|---|---|---|---|
  | dev | 156 / 4,070 | 156 / 4,032 | 120 / 3,060 | 114 / 2,893 | **114 / 2,583** |
  | test | 84 / 2,615 | 84 / 2,533 | 62 / 1,836 | 60 / 1,735 | **60 / 1,640** |
  | locked (after Oct 14) | 18 / 675 | 18 / 657 | 11 / 418 | 11 / 404 | 11 / 403 |

  The test set clears the gate's size floor (≥ 30 events, ≥ 300 markets), so the "data not feasible" STOP does not
  apply. Most of the 22 test events without a start time are TV interviews, which aren't on the calendar.
  **Vance:** 0 events have a start time. Factbase has no Vance calendar (`/factbase/vance/calendar/` redirects).
  Finding a source is M2 #3b; if none is found by the freeze, Vance is dropped, per Q3a.

**Incidents (logged honestly):** (1) While checking API field names, one raw test-period market record
(KXTRUMPMENTION-26SEP03-VENE) was printed with its `result` field. It was not analysed or used, and later inspections
left `result` out. (2) Two batch runs stopped partway: Claude stopped one on purpose to switch the DB to WAL so the
two batches could share it, and the other hit the batch endpoint's 10,000-candle cap. Both resumed without duplicate
fetches. Their `runs` rows are missing because they exited early. (3) Claude first committed `egg-info` and a SQLite
journal file by mistake. This was fixed by amending before any push.

**⭐ Evidence → decision → consequence:** Factbase listed rallies as "Pool Report" (evidence) → Claude widened the
schedule rule from "Official Schedule only" to "event entries under any tag, minus movements" and checked it on dev
only (decision) → 120 of 156 dev and 62 of 84 test events now have a start time, up from 105 / 55. The
rallies, the most typical mention-market events, are now included (consequence). The test-set mapping used no
outcomes or close times.

**AI use + Ian's judgment:**
- Ian's prompt: start S1, keep the dev/test split, paced reads only, show a plan first if s1-plan.md is out of date.
  Ian's reply to the plan: "Approve, start M1" (accepted as proposed, including locking the post-Oct-14 events and
  the keyword event types).
- Claude (Opus 5.5) wrote all the code, tests, event-matching rules and this entry. Rules Ian hasn't reviewed yet: the
  schedule-matching heuristic (score ≥ 0.5, movement entries dropped; full list in `event_map.csv`), the matcher's
  heuristics (adjective suffixes get no plural, a small irregular-plural list, Dr./Mr. abbreviations), and using the
  last sparse candle with no staleness limit. **Ian's verdict:** pending.

**Next (M2, Nov 12–15):** Vance source search (#3b); event-type keyword rules (logged as an AI input); base-rate
model v1 on **dev only**, with the look-ahead guard (transcript date < event date); reliability on dev; tuning;
freeze Nov 16 → ask Ian before scoring the test set.

---

## 2026-11-09 (later) — S1 M2 started early: Vance source, event types, base-rate model v1 on dev only

**Work** (Ian: "Start M2"): Kalshi milestones collector (`collect-milestones`), event-type keyword rules
(`event_types.py`), base-rate model v1 (`model.py`), dev-only tuning and backtest (`backtest.py`, `bloodhound tune-dev`),
a faster matcher that gives the same results (`count_matches_indexed`), and 79 new tests (`tests/test_model.py`):
175 pass + 5 expected failures. Reports: `docs/results/dev-backtest-2026-11-09.md` (and `-gap2`). **Only dev outcomes
were read** (`db.outcomes("dev")`); test and locked stay locked.

**Vance (#3b):** Kalshi's own `/milestones` give start times for 37/39 dev and 32/32 test Vance events, and on Trump
dev events they match Factbase closely (median 0 min). But no Vance **transcript** list exists on Factbase, so there's no
base rate. Recommendation: drop Vance for S1 per Q3a (`docs/evidence/s1-2026-11-09/vance_source.md`).

**Model v1:** P(word) = share of the last N earlier comparable transcripts containing the word (with the market's
"3+ times" threshold), shrunk to a prior mean m with strength s. Look-ahead guard: only transcripts dated before the
event's ET date (asserted in code and tests). Dev split by event date: **dev-A** (first 57 events, 1,145 markets)
picks the parameters from a 270-combination grid (pool, N, min speech length, s); **dev-B** (last 57 events, 1,438
markets) checks them. A second candidate, the **blend**, is a logistic fit on dev-A of logit(p_mkt) and logit(p_base).

| dev-B (not used for fitting) | Brier model | Brier market | model − market [95% CI] |
|---|---|---|---|
| base rate alone (all events, last 5, ≥ 15 min speech, s = 8) | 0.2302 | 0.1609 | +0.069 [+0.054, +0.085] |
| blend (market + base rate) | 0.1614 | 0.1609 | +0.0004 [−0.002, +0.003] |

Same picture with a 2-day transcript gap (in case transcripts post late): +0.073 and +0.0012.

**⭐ Evidence → decision → consequence:** the base rate alone lost badly on dev (evidence). Claude checked for a bug
before accepting it: the raw hit rate rises steadily with the outcome (YES 25% when the word was in none of the last 20
transcripts → 69% when in most), but ranks markets much less well than the price (AUC 0.68 vs 0.84). The grid
picks heavy shrinkage. So it's a weak real signal, not a broken matcher. Words Kalshi picks are often topical
to the event ("Artemis" at an Artemis event), which past speeches can't see but the market can (decision: report it
as is; offer a market+base-rate blend as the alternative freeze candidate) → the plan as written (base rate alone)
would almost surely hit the STOP rule on test; the blend ties the market on dev-B (consequence: the freeze choice is
Ian's, below).

**AI use + Ian's judgment:**
- Claude (Opus 5.5) wrote the event-type rules (logged in `docs/evidence/s1-2026-11-09/ai_inputs.jsonl`), the model,
  the tuning grid, the dev-A/dev-B split, the blend idea and this entry. **Ian's verdict:** pending on the event-type
  rules, on dropping Vance, and on which candidate to freeze.

**Next:** Ian picks the freeze candidate (blend or base alone; optionally one more pre-declared dev-only feature,
e.g. "word appears in the event title", tried Nov 12–15). Freeze Nov 16 with the hash in `decisions.md` → Ian's OK →
test scored once.

---

## 2026-11-09 (evening) — Model frozen: blend-v1

**Work:** Ian chose "Freeze the blend". Claude added:
- the frozen-model file (`docs/results/frozen_model.json`);
- the scorer, `bloodhound score --period dev|test|locked`, which gives the gate verdict per spec v2 and writes a
  dated report;
- a corpus fingerprint;
- a "scored once" marker.

The outcome guard now checks that the model files are byte-identical to the freeze commit, rather than requiring
HEAD to *be* the freeze commit. That way `decisions.md` can record the hash after the freeze. New tests run against a
throwaway git repo. Total: 185 pass, plus the 5 expected failures. Freeze commit
[`bb92f3a`](https://github.com/idownham/alt-edge/commit/bb92f3a23e843af48993bbfac12490aa7189f785), recorded in
`decisions.md`.

**Observation:** the frozen blend scored on all of dev reads 0.1633 vs the market's 0.1648 (−0.0015, 95% CI
[−0.0039, +0.0010]). That is in-sample on dev-A and out-of-sample on dev-B. The dev-B part alone is +0.0004, so the
test result will most likely be STOP or INCONCLUSIVE. This is written down before the test is scored.

**Decision:**
- The blend is frozen. Its parameters are kept exactly as validated on dev-B; there is no refit on all of dev. Claude
  chose this so the frozen model is the one that was checked.
- The freeze moved from Nov 16 to Nov 9.
- Vance is dropped for S1.

**AI use + Ian's judgment:** Claude proposed the blend, the no-refit choice and the guard change. Ian **accepted**
the blend ("Freeze the blend"). His verdicts on the event-type rules and on dropping Vance are still pending.

**Next:** Ian's OK → `bloodhound score --period test --score-test --frozen-hash bb92f3a` (once) → PASS / STOP /
INCONCLUSIVE → write-up.

---

## 2026-11-09 (night) — ⭐ Test set scored once: INCONCLUSIVE

**Work:** with Ian's OK ("Score test now"), the frozen blend (`bb92f3a`) was scored **once** on the held-out test set.
The guard accepted the freeze hash and the corpus fingerprint. Report `docs/results/score-test-2026-11-10.md` (UTC
date in the name).

| Test (60 events / 1,640 markets) | Brier model | Brier market | diff [95% CI] |
|---|---|---|---|
| frozen blend | 0.1614 | 0.1631 | −0.0017 [−0.0043, +0.0010] |
| base rate alone (reported only) | 0.2336 | 0.1631 | +0.0706 [+0.054, +0.087] |

**Observation:**
- The test result matches what was written down before scoring: likely STOP or INCONCLUSIVE.
- The blend is slightly better than the market, but not provably so.
- The market's own reliability on test is a little high in the 0.3–0.7 range. For example, the 0.4–0.5 bin has a
  mean price of 0.446 and a YES rate of 0.323. The blend pulls those prices down a bit.
- By event type the differences are small and mixed, with few events per type.
- The transcript base rate alone is clearly worse than the market (dev and test agree).

**⭐ Evidence → decision → consequence:** the test diff is −0.0017 with a CI crossing 0 (evidence). The spec's
pre-registered INCONCLUSIVE rule applies, with no re-tuning (decision). The one extension runs: the same frozen model
is scored on events through 2026-11-20, then PASS/STOP on test + extension together. The base rate's weak standalone
showing is recorded as a finding, whatever the final verdict (consequence).

**AI use + Ian's judgment:** Claude ran the scorer and wrote this entry. Ian **accepted** scoring now. Ian still
needs to confirm the pooling rule for the extension before the locked outcomes are read.

**Next (after Nov 20 markets settle, ~Nov 21):**
1. Run `collect-markets`, then `collect-schedule --refresh-last`, `map-events`, `collect-prices` and
   `collect-transcripts`.
2. Score the locked period once, then the pooled test + locked verdict.
3. Write-up by Nov 22.
