# alt-edge (Project Bloodhound) — underpriced prediction markets

## What this is
Research into whether careful homework (historical base rates from transcripts, exact rule wording, event context,
live updating) produces better-calibrated probabilities than the market price — starting with **mention markets**.
Owner: Ian Downham (GitHub: idownham). Shared portfolio rules: `../CLAUDE.md` (alt-hq).

## Current stage
**S1 — data pipeline + first predictor (started 2026-11-09, Ian's go; dates in `docs/decisions.md`).** M1 (pipeline,
rule-aware matcher, scoring code, counts only) Nov 9–12 → M2 (transcripts, base-rate v1 on **dev only**, tuning,
Vance source) Nov 12–15 → **freeze Nov 16** → test set scored **once** after Ian's OK. Test and post-Oct-14 ("locked")
outcomes are refused by `db.outcomes()` unless `--score-test` + the frozen hash. Criteria v2 (`docs/spec.md`, confirmed
2026-10-14) unchanged. All collection is hand-run, paced batches (`bloodhound collect-*`); nothing runs continuously;
`bloodhound status` reports counts. **Frozen 2026-11-09: blend-v1, commit `bb92f3a`** (`docs/results/frozen_model.json`, `decisions.md`); Vance dropped.
Next: test scored **once** with `bloodhound score --period test --score-test --frozen-hash bb92f3a`, only after Ian's OK. Plan: `docs/s1-plan.md`. S0 findings: `docs/s0-research.md`. Update this
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
- Python 3.11+, `pyproject.toml`, `.venv/` (`pip install -e '.[dev]'`), `pytest`. Small, focused commits. Stdlib only;
  HTTP goes through `curl` (python.org's macOS build has no CA bundle). Data in `data/` (DB + caches gitignored).
- `docs/journal.md` entry every session (work, evidence, observation, decision, AI use + Ian's judgment);
  `docs/decisions.md` for dated owner decisions.
- A `status` command is required once anything runs continuously (HQ's `/health` calls it).
