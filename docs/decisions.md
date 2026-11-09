# Decisions (alt-edge / Project Bloodhound)

Dated owner decisions. Newest last.

---

## 2026-10-14 — Plan Project Bloodhound
**Decision (Ian):** new project to find undervalued opportunities across prediction markets, starting with mention
markets ("What will Trump say?"). Code name Bloodhound, repo alt-edge.
**Start trigger:** a slot opens — Coin Toss recording done (~Oct 22) or Osprey Decision A = STOP.
**Gate:** calibration backtest (model beats market Brier score out-of-sample) before any money.

---

## 2026-10-14 — Start S0 early (before the planned trigger)
**Decision (Ian):** start S0 (research + lock the criteria) today, 2026-10-14, even though the planned start trigger
(Coin Toss recording done ~Oct 22, or Osprey Decision A = STOP) has not happened.
**Reason:** so Bloodhound has dated evidence for the class's Oct 25 early-prototype checkpoint.
**Limit:** S0 stays read-only desk research. No continuously running collectors (no launchd/systemd/cron jobs, no
24/7 polling) until a slot opens. One-off, paced (≤ 1 req/s, back off on 429), unauthenticated reads of public
APIs are allowed. No keys, no order code. Pre-registered criteria stay DRAFT until Ian approves them.

---

## 2026-10-14 — Pre-registered criteria v2 confirmed (before any outcome data)
**Decision (Ian):** criteria v2 in `docs/spec.md` are confirmed, with these answers to Q1–Q9 (`docs/s1-plan.md`).
No outcome data had been analysed when this was decided.
- **Q1 Benchmark time:** T_ref = Factbase scheduled start − 15 min. Accepted as proposed.
- **Q2 Quote filter:** two-sided quote and yes spread ≤ 10¢ at T_ref. Accepted.
- **Q3 Scope:** *revised.* **KXTRUMPMENTION is primary and alone decides PASS/STOP. KXVANCEMENTION is secondary**:
  scored and reported separately under the same rules, and it doesn't change the gate verdict. If no usable Vance
  transcript or start-time source is found by the model freeze, Vance is dropped and that is noted; the gate isn't
  blocked. Also added: **explore more mention series** as later iteration work, outside the gate.
- **Q4 Factbase:** allowed, with limits: ≤ 1 page / 2 s, fetched once and cached locally (gitignored), used for
  research only, not redistributed, not used to train models.
- **Q5 Split:** test = events whose first market closed 2026-06-01 → 2026-10-14; dev = earlier. Accepted.
- **Q6 Significance:** event-clustered bootstrap 95% upper bound of (model − market Brier) < 0. Accepted.
- **Q7 Paper gate:** top-half predicted-edge trades' net P&L per trade ≥ bottom half's. If Nov 22 arrives before
  50 trades / 10 events, report **INCOMPLETE** (thresholds not lowered) and keep going after the class.
- **Q8 Paper size:** 5 contracts per paper trade (changed from the proposed 10 after the thin top-of-book snapshot).
- **Q9 Fees:** Ian checked kalshi.com/fee-schedule on 2026-10-14: taker 0.07·C·P·(1−P), ceil to the cent; no maker
  fee on `quadratic` series.
**Change rule:** any later change to these criteria is recorded here, with the reason, before it is applied.

---

## 2026-11-09 — S1 started: new build dates; post-Oct-14 events locked; keyword event types
**Context:** the slot opened when Osprey's Decision A came out STOP (2026-10-28). Ian asked on 2026-11-08 to start S1.
The old S1 targets in `s1-plan.md` (Oct 25 prototype, Nov 8 test) have already passed.
**Decision (Ian, 2026-11-09, approving Claude's proposed plan):**
- **New build dates:** Milestone 1 (data pipeline, word matcher, scoring code, counts only) Nov 9–12. M2 (transcripts, base-rate
  v1 on dev only, tuning, Vance source decision) Nov 12–15. **Freeze Nov 16**, with the commit hash recorded here. Test
  set scored once, after Ian approves, Nov 16–17. Write-up Nov 17–22.
- **The pre-registered criteria do not change.** The inconclusive extension still runs through 2026-11-20 and the
  time box is still 2026-11-22. Because of the later start, a PASS will almost certainly leave the paper gate
  **INCOMPLETE** on Nov 22, as Q7 already allows.
- **Events whose first market closed after 2026-10-14** are in neither dev nor test. They are **locked like the test
  set**: never used for tuning, and used only for the one inconclusive extension (spec: new events through 2026-11-20).
- **Event type** (a model input) comes from fixed keyword rules on event titles (public before the event). Claude
  writes and checks the rules on dev titles only, and they are logged as an AI-produced input (`CLAUDE.md` rule 4).
**No outcome data had been analysed when this was decided.**
