"""Event type from fixed keyword rules (decision 2026-11-09). A model input, written by Claude (AI) from
dev-period Kalshi titles and Factbase transcript titles only, so it is logged as an AI-produced input in
docs/evidence/s1-2026-11-09/ai_inputs.jsonl (CLAUDE.md rule 4). Titles are public before each event.

The same rules type both sides: Kalshi event titles ("Press Conference at the NATO summit") and Factbase
transcript titles ("Roll Call Factba.se - Speech: Donald Trump Holds a Rally in ..."). The first matching
rule wins; anything unmatched is "remarks".
"""
from __future__ import annotations

import re

RULES_VERSION = "event-types-v1 (2026-11-09)"
TYPES = ("rally", "interview", "press_conference", "bilateral", "address", "remarks")

RULES: tuple[tuple[str, str], ...] = (
    ("rally", r"\brally\b|tele-?rally|turning point|build the red wall"),
    ("interview", r"interview|\bvlog\b|fox news|fox business|\bcnbc\b|newsmax|60 minutes|\bcbs\b|\bnbc\b|\babc\b"
                  r"|\bcnn\b|msnbc|podcast|radio|\bshow\b|kudlow|ingraham|futures|tonight|town hall|squawk"
                  r"|primetime|hannity|evening news|the story with"),
    ("press_conference", r"press conference|news conference|gaggle|press briefing|speaks? (briefly )?to reporters"
                         r"|cabinet meeting|q&a"),
    ("bilateral", r"bilateral|\bmeets? with\b|\bmeetings? with\b|visit with the|greeting with|holds a meeting with"
                  r"|\bmeeting\b.*\b(president|prime minister|king|chancellor)\b"),
    ("address", r"address|\bspeech\b|commencement|keynote|state of the union|general assembly|prayer breakfast"),
)
_COMPILED = tuple((t, re.compile(p, re.I)) for t, p in RULES)
_FACTBASE_PREFIX = re.compile(r"^roll call factba\.se\s*-\s*", re.I)


def classify(title: str | None) -> str:
    t = _FACTBASE_PREFIX.sub("", title or "")
    for typ, rx in _COMPILED:
        if rx.search(t):
            return typ
    return "remarks"
