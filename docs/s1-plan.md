# S1 plan — approved scope (2026-10-14); **started 2026-11-09**

> **2026-11-09 update (Ian approved, `decisions.md`):** the dates below were out of date (the slot opened 2026-10-28;
> S1 started 2026-11-09). New build dates: **M1** pipeline + matcher + scoring code, counts only, Nov 9–12 · **M2**
> transcripts, base-rate v1 on dev, tuning, Vance source decision, Nov 12–15 · **Freeze Nov 16** · test scored once
> after Ian's OK, Nov 16–17 · write-up Nov 17–22. The dates in the criteria (extension through Nov 20, time box
> Nov 22) are unchanged. Events after 2026-10-14 are locked like the test set. The original timeline table is kept
> below for the record.
>
> **M1 status (2026-11-09):** done: #1 collector, #2 schedule mapping + T_ref prices (Trump), #4 matcher (all
> contract examples as tests), the scoring/fee code from #6 (tested, not yet run on outcomes), #7 `status`. Code in
> `src/bloodhound/`, run as `bloodhound <command>`. #3 transcripts collected early (1,252 calendar-linked pages, Jan 2025 →
> Nov 8 2026; the calendar has no 2024). After filters: Trump dev 114 ev / 2,583 mkts, test 60 / 1,640. Not done yet: #3b Vance source (Factbase has no
> Vance calendar: `/factbase/vance/calendar/` redirects), #5 model.

> **M2 status (2026-11-09, started early):** #3b Vance: start times found (Kalshi milestones), no transcript list →
> recommend dropping Vance for S1 (`evidence/s1-2026-11-09/vance_source.md`). #5 base-rate v1 + #6 dev backtest done
> (`docs/results/dev-backtest-2026-11-09.md`): on dev-B the base rate alone loses to the market (Brier 0.230 vs
> 0.161); a market + base-rate blend ties it (0.1614 vs 0.1609). **Frozen 2026-11-09** (Ian: blend), commit `bb92f3a`; test not yet scored.

*Proposed by Claude at the end of S0. Ian answered Q1–Q9 and confirmed criteria v2 on 2026-10-14 (`decisions.md`).
Per the 2026-10-14 decision, nothing runs continuously before a slot opens. Every step below is a **one-off batch
job** run by hand, paced at ≤ 1 req/s with a 10 s back-off on 429. That leaves room for the Coin Toss and Slot Machine
recorders on the same laptop IP.*

## Smallest build that answers the question

| # | Piece | What it does | Size / load |
|---|---|---|---|
| 1 | **Market + rules collector** (`bloodhound collect-markets`) | Pulls every settled KXTRUMPMENTION and KXVANCEMENTION market (live + historical endpoints) into SQLite: ticker, event, word, full `rules_primary`/`rules_secondary`, open/close times, result. Results go in a column the dev tools can read only for dev-set events (see guard in #5). | ~10 requests |
| 2 | **Schedule + reference prices** (`collect-schedule`, `collect-prices`) | Reads Factbase monthly calendar pages for scheduled start times, maps them to Kalshi events (by hand where titles differ, stored as a CSV with notes), then pulls one 1-minute candle window around T_ref per market. | ~19 calendar pages; ~8,500 candle requests (Trump + Vance) ≈ 2.5 h at 1 req/s, run once, resumable |
| 3 | **Transcript corpus** (`collect-transcripts`) | Factbase transcripts for Trump events from 2024-01 on (base-rate history before the first market), stored as text with segment timestamps and event date. Polite: ≤ 1 page per 2 s, cached once in `data/transcripts/` (gitignored), never redistributed or used for training (Q4). | a few hundred pages |
| 3b | **Vance source search** (secondary) | Find a free Vance transcript + start-time source (check Factbase first, then official/C-SPAN pages); record coverage and terms in `s0-research.md`. If nothing usable by the freeze, drop Vance and note it (Q3a). | desk research |
| 4 | **Rule-aware word matcher** | Applies the MENTION.pdf rules: plural/possessive yes; other inflections no; open/hyphen compounds yes; closed compounds no; slash alternatives; numbers. Unit tests built from **every example in the contract PDF**. | pure code + tests |
| 5 | **Base-rate model v1** | P(word) = share of the speaker's last N comparable events (same type, earlier dates only) containing the word, shrunk with a Beta prior fit on the dev set. Event type comes from a hand-labelled map. A look-ahead guard asserts that every transcript date is < event date, and the test-set results stay locked until a `--score-test` flag is used with a frozen commit hash. | small |
| 6 | **Calibration backtest** | Brier / log loss / reliability for model vs p_mkt on dev; on test **once**; event-clustered bootstrap. Writes a dated report to `docs/results/`. | small |
| 7 | `status` command | Reports DB counts and the last batch run. Required by `CLAUDE.md` once anything runs on a schedule; added early so HQ `/health` can call it. | tiny |

Live updating (edge source 4) is **out of S1**; it's an iteration candidate only if the gate passes.

**Explore more mention series (Ian, Q3; iteration work, outside the gate).** After the Nov 8 gate result, survey the
other series in `evidence/s0-2026-10-14/mention_series.csv` for the next candidates. Look at the Press Secretary, Fed
Chair, earnings calls, NFL announcers and hearings: events per month, free transcript source, and rule quirks. This is
counts, rules and sources only. Any new series gets its own pre-registered criteria before its outcomes are looked at.

## Timeline against class dates

| Dates | Work | Class checkpoint |
|---|---|---|
| Oct 15–17 | Ian approves the criteria and answers Q1–Q9 (dated entry in `decisions.md`). Scaffold `pyproject.toml`, SQLite schema, collector #1, matcher #4 with contract-example tests. | |
| Oct 18–22 | Schedule mapping #2 and transcript corpus #3 (dev-period events first). Price pull #2. Vance source search #3b. All one-off batches. | |
| Oct 23–25 | Base-rate v1 on the **dev set only**: reliability table, model vs market on dev. Demo: rule-aware matcher + base rate for one upcoming rally. | **Oct 25 early prototype** |
| Oct 26–Nov 4 | Tune on dev (event-type map, lookback N, prior). Look-ahead tests. **Freeze**: commit hash recorded in `decisions.md`. | |
| Nov 5–8 | Score the held-out test set **once** → PASS / STOP / inconclusive per `spec.md`. Write it up with the evidence. | **Nov 8 working build + test** |
| Nov 9–22 | Explore more mention series (survey only). If PASS: forward paper trades reconstructed from public candles on events listed after the freeze. About 16 events/month means only ~8–10 events by Nov 22, so the paper gate (≥ 10 events) may finish just after. If STOP: write up "no demonstrated edge", with what the rule-reading did and didn't show. If inconclusive: the one allowed forward extension through Nov 20. | **Nov 22 iteration + story** |
| Dec 1 / Dec 4 | Rough cut / final package from the journal. | |

If the Coin Toss slot opens Oct 22 as planned, nothing changes: S1 needs no continuous collector until the paper
stage, and even that can be rebuilt from candles.

## Questions for Ian — ANSWERED 2026-10-14 (see `decisions.md`)

Answers: Q1 −15 min ✔ · Q2 ≤ 10¢ ✔ · Q3 *revised*: Trump primary + Vance secondary, explore more series later ·
Q4 yes, with the limits ✔ · Q5 test from 2026-06-01 ✔ · Q6 95% ✔ · Q7 top half ≥ bottom half; INCOMPLETE if the
deadline hits ✔ · Q8 5 contracts (changed from 10) · Q9 fee checked by Ian: 0.07, no maker fee ✔.

Original questions, kept for the record:

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
