# alt-edge (Project Bloodhound) — underpriced prediction markets

## What this is
Research into whether careful homework (historical base rates from transcripts, exact rule wording, event context,
live updating) produces better-calibrated probabilities than the market price — starting with **mention markets**.
Owner: Ian Downham (GitHub: idownham). Shared portfolio rules: `../CLAUDE.md` (alt-hq).

## Current stage
**S0 — research + lock the criteria (started early 2026-10-14, see `docs/decisions.md`).** Read-only desk research
only; no continuously running collectors until a slot opens (Coin Toss recording done ~Oct 22, or Osprey Decision A
= STOP). Findings: `docs/s0-research.md`. Criteria in `docs/spec.md` stay DRAFT until Ian approves them. Update this
line when the stage changes.

## Hard rules
1. **Read-only research.** No order code until a calibration backtest passes and Ian records a dated decision.
2. **Calibration before money.** Model probabilities must beat the market's closing-price Brier score
   out-of-sample (criteria in `docs/spec.md`, confirmed by Ian before data is analysed).
3. **Rules are data.** Every market's exact resolution rules (word forms, who must say it, event window, source)
   are stored with the market and applied when matching transcripts. Never assume the title says it all.
4. **AI estimates are logged, not trusted.** Any probability or rule interpretation produced by an AI is stored
   with the prompt, model, and timestamp, and scored like any other forecast.
5. **No look-ahead.** Backtests use only transcripts and prices available before each market closed.
6. Money as Decimal or integer cents. Secrets only in `.env`.

## Conventions
- Python 3.11+, `pyproject.toml`, `.venv/`, `pytest`. Small, focused commits.
- `docs/journal.md` entry every session (work, evidence, observation, decision, AI use + Ian's judgment);
  `docs/decisions.md` for dated owner decisions.
- A `status` command is required once anything runs continuously (HQ's `/health` calls it).
