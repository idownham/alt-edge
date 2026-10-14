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
