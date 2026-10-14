# S0 research — Kalshi mention markets (2026-10-14)

*Status: S0 desk research, done 2026-10-14 (started early, see `decisions.md`). Read-only: about 60 unauthenticated,
paced (≤ 1 req/s) Kalshi public API calls, plus public web pages. No keys. **No outcome data was analysed.** No YES/NO
rates, Brier scores or price-vs-result comparisons were computed. Counts, volumes, rules and prices-without-results only.*

Evidence files: `docs/evidence/s0-2026-10-14/` (the series list, per-series counts, rule samples, the historical cutoff
response). The fetch helper is `scripts/s0_kget.py`; raw responses went to `data/raw/` (gitignored).
"API" below means `https://api.elections.kalshi.com/trade-api/v2`, with fetch times in UTC.

## Bottom line

**Feasible, with one big change to the draft criteria.**

1. There is plenty of data. `KXTRUMPMENTION` alone has **6,858 resolved markets in 241 events**, from 2025-04-02 to
   2026-10-14. Old markets come with rules, results, 1-minute bid/ask candles and full trade history, all from public
   endpoints. ≥ 100 markets is easy. The real limit is **events** (markets in one event are correlated), so the gate
   should count events too.
2. Free transcripts exist for the biggest speaker. Roll Call Factbase has same-day Trump transcripts with speaker
   labels and per-segment timestamps, plus a public schedule with start times. Its terms of use are unclear (Q below).
3. ⚠️ **The draft benchmark ("market's closing price") is broken for these markets.** Every market has
   `can_close_early: true`, and the condition reads *"This market will close and expire early if the event occurs."*
   So a YES market closes right after the word is said, with its last price at about $0.99. Example: KXTRUMPMENTION-26OCT14-TSMC,
   `last_price_dollars` "0.9900", closed 22:24:31Z (API `/markets`, fetched 2026-10-14T23:29:10Z). A closing-price
   Brier score would contain the answer. **The benchmark has to be the price at a fixed time *before* the event
   starts.** The API has no event start time, so it has to come from an outside schedule (Factbase calendar).
   → This is an **evidence → decision → consequence** moment (see journal).

## 1. Which Kalshi series are mention markets

Source: `GET /series?category=Mentions`, fetched 2026-10-14T23:28:41Z → **459 series** (one page, no cursor). Full list:
`evidence/.../mention_series.csv`.

- **fee_type:** all 459 are `quadratic`, `fee_multiplier` 1. None is `quadratic_with_maker_fees`. Taker fee =
  ceil-to-cent(0.07 × C × P × (1−P)), so 1.75¢/contract at 50¢ and 0.63¢ at 10¢. Osprey confirmed the 0.07
  coefficient against Kalshi's fee-schedule PDF on 2026-10-13 (`../project-osprey/docs/plan.md`). The PDF blocked
  automated download here (HTTP 429, 2026-10-14), so it is **not re-quoted**. No maker fee on `quadratic` is inferred
  from the `fee_type` naming, as in Slot Machine's S0. *Ian: a 1-minute browser check of kalshi.com/fee-schedule is
  worth doing.*
- **Contract templates** (`contract_terms_url`): MENTION.pdf 202, EARNINGSMENTION.pdf 179, TRUMPMENTION.pdf 20,
  MENTIONEARN.pdf 13, TRUMPSAY.pdf 9, others < 8.
- **Tags:** Earnings 192, Politicians 61, Business 42, Sports 17, Trump 12, Entertainment 7.
- Many series are tiny or one-offs (e.g. `KXANVCD`, title "dvdvsfv", looks like a test listing). Activity is
  concentrated in a few.

Activity for the series pulled in full (settled markets from `/markets?status=settled` plus `/historical/markets`, fetched
2026-10-14 23:29–23:30Z; `evidence/.../series_stats.txt`):

| Series | What | Resolved markets | Events | First → last close | Median volume / market (contracts) | Events / month (Jan–Sep 2026) |
|---|---|---:|---:|---|---:|---:|
| KXTRUMPMENTION | Trump at a named event (rallies, remarks, pressers) | 6,858 | 241 | 2025-04-02 → 2026-10-14 | 15,416 | 16.3 |
| KXTRUMPSAY | Trump says X **anywhere, incl. Truth Social** before a date | 1,698 | 58 | 2025-08-08 → 2026-10-14 | 24,988 | 4.4 |
| KXVANCEMENTION | JD Vance at an event | 1,679 | 71 | 2025-07-17 → 2026-10-09 | 6,846 | 6.1 |
| KXSECPRESSMENTION | WH Press Secretary, next briefing | 1,549 | 64 | 2025-01-31 → 2026-10-13 | 8,222 | 2.0 |
| KXNFLMENTION | NFL broadcast announcers | 1,543 | 71 | 2025-09-30 → 2026-04-24 | 18,856 | 2.7 |
| KXMENTION | generic "What will someone say?" | 871 | 57 | 2026-03-09 → 2026-03-19 | 5,073 | 6.3 |
| KXHEARINGMENTION | congressional hearings | 849 | 53 | 2026-04-14 → 2026-09-15 | 2,714 | 5.9 |
| KXFEDMENTION | Fed Chair post-FOMC presser | 545 | 14 | 2025-01-30 → 2026-09-16 | 23,226 | 0.7 |
| KXMRBEASTMENTION | MrBeast's next video | 451 | 27 | 2025-08-17 → 2026-08-08 | 5,608 | 1.8 |
| KXEARNINGSMENTIONNVDA / TSLA | one company's earnings call | 128 / 125 | 7 / 6 | 2025 → 2026 | 10,614 / 8,360 | 0.3 each |

How often new events list: KXTRUMPMENTION lists about **16–20 events a month** in 2026 (events by open month: Jan 17,
Feb 18, … Jul 20, Aug 19, Sep 19), with a median of 25–30 words per event. Markets are created about a day ahead:
the Oct 14 rally markets were created 2026-10-13T22:34Z and opened 22:45Z. On 2026-10-14T23:32Z there were
76 open markets across 3 upcoming Trump events.

**Depth.** Volume is high: median about 15k contracts per Trump market, and 99.9% of recent markets traded ≥ 1,000.
Quoted size at the top of the book is thin, though. Snapshot 2026-10-14T23:32:50Z, three days before the Oct 17
Kentucky rally (`/markets/{t}/orderbook`):
`…26OCT17-FENT` yes bid 0.15 (1.24 contracts at best) / ask 0.16; `…-CRYP` 0.01/0.02; `…-OIL` 0.96/0.98. Spreads are
1–2¢ with tens of contracts at the best price. That's fine for a small paper test. One snapshot isn't a depth study.

**Recommendation for S1 scope:** **KXTRUMPMENTION only** for the calibration gate. It has the most events, a single
speaker, Factbase transcripts and a public schedule. Leave out KXTRUMPSAY: its rules count Truth Social posts and
quotes from 18 news outlets, which needs a different corpus. Vance, the Press Secretary and the Fed Chair are candidate
second series later.

## 2. Rule wording (word matches, speaker, window, source)

Two layers: the per-market `rules_primary`/`rules_secondary` (API) and the series' contract-terms PDF.

**Contract-terms PDF** (`https://assets.kalshi.com/contract_terms/MENTION.pdf`, downloaded 2026-10-14T23:30Z; the
document's header reads "NEWMENTION"; `TRUMPSAY.pdf` has the same matching rules). Key matching rules, in brief:
- Plural and possessive noun forms count. Other inflections don't ("Immigrant" → "Immigration" no; "Run" → "Ran" no).
  If the word is given as a plural, the singular doesn't count ("Veterans" → "Veteran" no).
- **Compounds:** open ("fire station") and hyphenated ("pro-Palestine") compounds count. **Closed compounds don't**
  ("wildfire", "firefighter"). Ties are settled by Merriam-Webster **and** the OED; listing in either as open or
  hyphenated is enough.
- Homographs count regardless of meaning ("Apple" the fruit counts for Apple; "Will" counts in "I will go").
  Homophones don't ("right" ≠ "write"). Minor mispronunciations count ("Mandani" for "Mamdani").
- Slash strikes: either word counts ("Doge/Dogecoin").
- Numbers spoken as words count exactly. Ordinal/cardinal rules apply. Acronym expansions don't count
  ("artificial intelligence" ≠ "AI").
- `<entity>` defined by a title tracks whoever holds the post; AND/OR lists of speakers are allowed.
- A livestream event may stay open 24 h for the official recording. A postponement of ≤ 14 days, if announced by
  the next day, keeps markets open.

**Real markets' rules** (API, fetched 2026-10-14 23:29Z; full text in `evidence/.../rule_samples.json`):

1. **KXTRUMPMENTION-26OCT14-TSMC** (rally): *"If Donald Trump says TSMC as part of Midterm Rally in Bullhead City,
   Arizona originally scheduled for October 14, 2026, then the market resolves to Yes."* Source: *"Video … using the
   live broadcast or stream"*, then transcripts if Kalshi staff can't agree. Speaker: *"Donald Trump speaking in an
   official capacity"*. Hot-mic and private remarks are excluded, as are *"previously aired content, archival
   footage"*. An "Event does not qualify" strike settles YES if the event is cancelled.
2. **KXTRUMPSAY-26OCT19-AUTO**: *"If Autopen / Auto Pen, or a plural or possessive form … is stated by Donald Trump
   before Oct 19, 2026 at 12:00am ET"*. It counts *"written public statements on his personal social media accounts
   (Twitter/Truth Social)"* and direct quotes published by Source Agencies. Official acts like EOs don't count.
   **This window is several days, not one event.**
3. **KXSECPRESSMENTION-26OCT27-AFFO**: *"…at the next Press Briefing by the White House Press Secretary (does not
   include gaggles)"*. The event must be open to the press and broadcast live. The speaker is the office, not a named
   person.
4. **KXFEDMENTION-26SEP-GAS** ("Gas / Gasoline / Natural Gas"): the window is *"his Sep 2026 post-FOMC meeting
   introductory remarks and Q+A"*. The speaker is *"the Chair of the Federal Reserve"*.
5. **KXEARNINGSMENTIONNVDA-26AUG26-ARIZ**: *"…said by any NVIDIA Corporation representative (including the operator
   of the call) during the next NVIDIA Corporation earnings call (including the Q+A)"*. The operator counts.
   (Also KXNFLMENTION-DRAFT-BAD: a list of six named announcers with OR logic; commentary from broadcast start to the
   end of round 1; promos count, ads don't.)

**What the title doesn't tell you** (rule-reading edge candidates, and also pitfalls for our matcher): plurals count
but derivations don't; closed compounds don't count; slash strikes give several targets; who counts (operator,
office-holder, named OR-list); the window (one event vs "before date" including posts); and the event cutoff.
Rule 3 of `CLAUDE.md` ("rules are data") is confirmed as necessary.

## 3. Historical prices and outcomes from the public API

**Yes, back to January 2025, unauthenticated.**

- `GET /historical/cutoff` (2026-10-14T23:29:02Z): `market_settled_ts` and `trades_created_ts` = 2026-08-15. Markets
  settled before then are served only from `/historical/markets`; later ones come from `/markets?status=settled`
  (docs.kalshi.com "Historical data" page, read 2026-10-14). Both worked without keys.
- Market records keep `rules_primary`, `rules_secondary`, `custom_strike.Word`, `open_time`, `close_time`,
  `occurrence_datetime`, `result`, `volume_fp`, `last_price_dollars`. The oldest one seen: KXFEDMENTION, closed
  2025-01-30; KXTRUMPMENTION, 2025-04-02.
- **Candlesticks:** `/series/{s}/markets/{t}/candlesticks` (recent) and `/historical/markets/{t}/candlesticks` (old)
  return per-period yes_bid / yes_ask OHLC, trade price and volume. `period_interval` 1 / 60 / 1440 minutes, and
  **max 5,000 candles per request** (HTTP 400 above that, 2026-10-14T23:30:30Z). Tested on the oldest Trump market,
  KXTRUMPMENTION-25APR02-RIPOFF: 33 hourly candles with bid/ask present (2026-10-14T23:30:51Z).
- **Trades:** `/markets/trades?ticker=` and `/historical/trades?ticker=`. The same old market returned 370 trades,
  2025-04-01 → 2025-04-02 (2026-10-14T23:30:52Z).
- **Not in the API: event start time.** The event and metadata endpoints (`/events/KXTRUMPMENTION-26OCT14`,
  2026-10-14T23:31:02Z) give a title and sub-title ("… originally scheduled for October 14, 2026": a date, no time)
  and no start timestamp. `close_time` of NO markets and `occurrence_datetime` come after the event, so neither can
  be used as a pre-event reference without look-ahead.

## 4. Free transcript sources

| Source | Speakers | Coverage / latency (observed) | Format | Terms / caveats |
|---|---|---|---|---|
| **Roll Call Factbase** (rollcall.com/factbase) | Trump (also briefings, gaggles, interviews) | Calendar for Oct 2026 lists the Oct 14 Bullhead City rally *at 4:00 PM ET [1:00 PM local]* with a "Full Text and Analysis" link already present; Oct 1–13 events also linked (read 2026-10-14 ≈ 23:35Z) → **same-day**. | HTML; speaker-labelled segments with timestamps (e.g. "Donald Trump 00:00:00-00:00:05"), total duration (Oct 9 Columbus Day event: 3,559 s). | No terms of use page found (rollcall.com/terms-of-use → 404). Footer: "Copyright 2026 CQ and Roll Call. All rights reserved." robots.txt allows `*` but **disallows AI-training crawlers (incl. `anthropic-ai`)**. Our use is research fetching by Ian's scripts, not training, but **Ian should decide** (Q4). The URL slug guessed for Oct 14 returned 404, so links must be read from the calendar, not built by hand. |
| Federal Reserve | Fed Chair pressers | Transcript PDF at `federalreserve.gov/mediacenter/files/FOMCpresconf20260916.pdf`, Last-Modified 2026-09-24 → **~8 days after** the Sep 16 meeting (HEAD, 2026-10-14). The Sep 2025 one: 9 days. | PDF | Public US government work. |
| White House | Press Secretary briefings | In late May 2025 the White House began removing official transcripts from its site (secondary report, via rollcall.com factba-se page in web search 2026-10-14; not independently verified). Factbase covers briefings. | — | Not verified in S0. |
| Earnings calls | Company reps | Free transcripts are spread out (company IR webcasts, fool.com). Not tested in S0. | — | Out of S1 scope. |
| YouTube auto-captions | many | Not used. Automated access is outside YouTube's terms except via its API, and quality is uneven. | — | Rejected for S1. |

For the gate, **transcripts are only used for base rates from events *before* each market** (no look-ahead). So
same-day latency matters only for live updating. Historical coverage matters most, and Factbase's timeline goes back
years.

## 5. How many resolved markets are there for an out-of-sample test?

`KXTRUMPMENTION`, split by each event's first market close (counts only, no outcomes):

| Window | Events | Markets |
|---|---:|---:|
| 2025-04-02 → 2026-05-31 (development) | 157 | 4,114 |
| 2026-06-01 → 2026-10-14 (held-out test) | 84 | 2,744 |

Of these, 125 markets are "Event does not qualify" strikes. They must be excluded, since they aren't word markets.
Markets will also drop out where there's no two-sided quote at the reference time, or no Factbase start time. **≥ 100
markets is very realistic. ≥ 30 test events is realistic.** Event titles are messy: a keyword count gives about 23
"rally", 12 "press conference", 7 "interview" and 199 "remarks/other", so event type needs a hand-made map in S1.

## 6. Risks and unknowns found in S0

- **Benchmark contamination** (the bottom-line point). Fix: a pre-event reference time from the Factbase schedule.
- **Correlated markets.** About 28 words per event share one speech. Use event-clustered statistics.
- **Selection bias.** Kalshi picks which words to list, probably near 50/50 or topical. Base rates from "all words"
  don't apply directly; the model must be scored only on listed words.
- **Event-start uncertainty.** Trump often starts late. A fixed offset before the *scheduled* time is simple and free
  of look-ahead, but the price may already move if he's late (that's still pre-event information, so OK).
- **Thin top-of-book.** Paper fills must assume small size.
- **Transcript ≠ resolution source.** Kalshi resolves from video. Factbase transcript errors would add noise to *our*
  base rates, not to the outcomes, which come from the API.
- **Data endpoints can change.** The historical cutoff moves forward over time. Pull and store once.

## Sources

- Kalshi API (public, no auth), `https://api.elections.kalshi.com/trade-api/v2`: `/series?category=Mentions`,
  `/markets`, `/historical/markets`, `/historical/cutoff`, `/events/{t}`, `/events/{t}/metadata`, candlesticks,
  trades, orderbook. All fetched 2026-10-14 23:28–23:33Z, ≤ 1 req/s, no 429s.
- Kalshi contract terms: https://assets.kalshi.com/contract_terms/MENTION.pdf and `TRUMPSAY.pdf` (2026-10-14).
- Kalshi docs, historical data: https://docs.kalshi.com/getting_started/historical_data (read 2026-10-14, undated).
- Fee coefficient: `../project-osprey/docs/plan.md` (checked against the fee-schedule PDF 2026-10-13); kalshi.com
  fee PDF returned 429 here.
- Roll Call Factbase calendar: https://rollcall.com/factbase/trump/calendar/october-2026/ ; example transcript:
  https://rollcall.com/factbase/trump/transcript/donald-trump-speech-columbus-day-celebration-october-9-2026/ ;
  robots: https://rollcall.com/robots.txt (all 2026-10-14).
- Fed: https://www.federalreserve.gov/monetarypolicy/fomccalendars.htm and the presser PDF above (2026-10-14).
