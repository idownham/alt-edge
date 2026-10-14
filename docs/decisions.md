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
