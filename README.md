# alt-edge — Project Bloodhound

Find underpriced prediction markets by doing the homework other traders skip — starting with mention markets
("Will [person] say [word] during [event]?"): transcript base rates, rule fine print, event context, live updating.

**Status: S1 (started 2026-11-09).** Read-only data pipeline and calibration backtest; see `CLAUDE.md` for the stage.
Setup: `python3 -m venv .venv && .venv/bin/pip install -e '.[dev]'`, then `.venv/bin/bloodhound status`.
Plan: `docs/spec.md`. Rules: `CLAUDE.md`. Part of the `alt` portfolio — see [alt-hq](https://github.com/idownham/alt-hq).
