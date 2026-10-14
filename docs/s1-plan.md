# S1 plan — PROPOSED (2026-10-14), not started

*Proposed by Claude at the end of S0. S1 starts only when Ian approves the criteria (`spec.md` v2) and answers Q1–Q9.
Per the 2026-10-14 decision, nothing runs continuously before a slot opens. Every step below is a **one-off batch
job** run by hand, paced at ≤ 1 req/s with a 10 s back-off on 429. That leaves room for the Coin Toss and Slot Machine
recorders on the same laptop IP.*

## Smallest build that answers the question

| # | Piece | What it does | Size / load |
|---|---|---|---|
| 1 | **Market + rules collector** (`bloodhound collect-markets`) | Pulls every settled KXTRUMPMENTION market (live + historical endpoints) into SQLite: ticker, event, word, full `rules_primary`/`rules_secondary`, open/close times, result. Results go in a column the dev tools can read only for dev-set events (see guard in #5). | ~10 requests |
| 2 | **Schedule + reference prices** (`collect-schedule`, `collect-prices`) | Reads Factbase monthly calendar pages for scheduled start times, maps them to Kalshi events (by hand where titles differ, stored as a CSV with notes), then pulls one 1-minute candle window around T_ref per market. | ~19 calendar pages; ~6,900 candle requests ≈ 2 h at 1 req/s, run once, resumable |
| 3 | **Transcript corpus** (`collect-transcripts`) | Factbase transcripts for Trump events from 2024-01 on (base-rate history before the first market), stored as text with segment timestamps and event date. Polite: ≤ 1 page per 2 s, cached, never re-fetched. | a few hundred pages; Q4 first |
| 4 | **Rule-aware word matcher** | Applies the MENTION.pdf rules: plural/possessive yes; other inflections no; open/hyphen compounds yes; closed compounds no; slash alternatives; numbers. Unit tests built from **every example in the contract PDF**. | pure code + tests |
| 5 | **Base-rate model v1** | P(word) = share of the speaker's last N comparable events (same type, earlier dates only) containing the word, shrunk with a Beta prior fit on the dev set. Event type comes from a hand-labelled map. A look-ahead guard asserts that every transcript date is < event date, and the test-set results stay locked until a `--score-test` flag is used with a frozen commit hash. | small |
| 6 | **Calibration backtest** | Brier / log loss / reliability for model vs p_mkt on dev; on test **once**; event-clustered bootstrap. Writes a dated report to `docs/results/`. | small |
| 7 | `status` command | Reports DB counts and the last batch run. Required by `CLAUDE.md` once anything runs on a schedule; added early so HQ `/health` can call it. | tiny |

Live updating (edge source 4) and other speakers are **out of S1**. They're iteration candidates only if the gate passes.

## Timeline against class dates

| Dates | Work | Class checkpoint |
|---|---|---|
| Oct 15–17 | Ian approves the criteria and answers Q1–Q9 (dated entry in `decisions.md`). Scaffold `pyproject.toml`, SQLite schema, collector #1, matcher #4 with contract-example tests. | |
| Oct 18–22 | Schedule mapping #2 and transcript corpus #3 (dev-period events first). Price pull #2. All one-off batches. | |
| Oct 23–25 | Base-rate v1 on the **dev set only**: reliability table, model vs market on dev. Demo: rule-aware matcher + base rate for one upcoming rally. | **Oct 25 early prototype** |
| Oct 26–Nov 4 | Tune on dev (event-type map, lookback N, prior). Look-ahead tests. **Freeze**: commit hash recorded in `decisions.md`. | |
| Nov 5–8 | Score the held-out test set **once** → PASS / STOP / inconclusive per `spec.md`. Write it up with the evidence. | **Nov 8 working build + test** |
| Nov 9–22 | If PASS: forward paper trades reconstructed from public candles on events listed after the freeze. About 16 events/month means only ~8–10 events by Nov 22, so the paper gate (≥ 10 events) may finish just after. If STOP: write up "no demonstrated edge", with what the rule-reading did and didn't show. If inconclusive: the one allowed forward extension through Nov 20. | **Nov 22 iteration + story** |
| Dec 1 / Dec 4 | Rough cut / final package from the journal. | |

If the Coin Toss slot opens Oct 22 as planned, nothing changes: S1 needs no continuous collector until the paper
stage, and even that can be rebuilt from candles.

## Questions for Ian (decide before any outcome data is looked at)

1. **Benchmark time:** is T_ref = scheduled start − 15 min right? (Alternatives: −60 min; or the event's open price.)
2. **Quote filter:** exclude markets with no two-sided quote or a spread > 10¢ at T_ref. Is 10¢ OK?
3. **Scope:** KXTRUMPMENTION only for the gate (recommended), or also Vance / Press Secretary?
4. **Factbase:** OK to fetch transcripts and calendar pages from rollcall.com for this research (≤ 1 page / 2 s,
   cached, not redistributed, not used for training)? No terms page was found; robots.txt allows general crawlers
   but blocks AI-training bots. If no, the fallback is limited (Fed PDFs only cover the Fed series).
5. **Split:** dev ≤ 2026-05-31, test 2026-06-01 → 2026-10-14. OK? (The test set is 84 events before filters.)
6. **Significance:** require the 95% event-clustered bootstrap bound < 0, or accept a point-estimate win with a 90%
   bound? Stricter means a higher chance of an "inconclusive" result.
7. **Paper gate:** "edge where the model predicted it". Is "top-half predicted-edge trades do at least as well as the
   bottom half" a precise enough test? And should the paper gate allow fewer than 10 events if the class deadline
   hits first (reported as incomplete, not PASS)?
8. **Fill model for paper trades:** taker at the T_ref candle's ask/bid, 10 contracts. Top-of-book was 1–50 contracts
   in the one snapshot taken, so 10 may be optimistic at some prices. Keep 10 or use 5?
9. **Fee check:** can you open kalshi.com/fee-schedule in a browser once and confirm the 0.07 taker coefficient and
   no maker fee for `quadratic` series? (Automated download is blocked.)
