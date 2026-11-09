"""Rule-aware word matcher for Kalshi mention markets (contract terms MENTION.pdf, "NEWMENTION",
fetched 2026-11-09; per-market rules_secondary say the same in short).

Works on transcript TEXT, so rules that depend on pronunciation (mispronunciations, transliterations,
extended sung words, URLs read aloud, acronyms pronounced as words) are out of reach; see the
xfail tests in tests/test_matcher.py. Implemented:
- case-insensitive; the word must be a whole token; space- and hyphen-separated compounds count,
  closed compounds don't ("fire" in "fire station" / "pro-Palestine" yes, "wildfire" no);
- plural and possessive forms of the (last) word count; other inflections don't; a plural target's
  singular doesn't (we never generate singulars);
- adjective-looking targets (-ic, -ous, -ful, -less) get no plural ("Economic" -> "Economics" no);
- slash alternatives ("Doge/Dogecoin") - any one counts;
- numbers: digits <-> words, not inside a larger number; unit words ("trillion") count anywhere;
  ordinals count when the target is numeric or a phrase containing a number;
- a few abbreviations read as the full word ("Dr." -> Doctor) and letter-by-letter spelling
  ("N-A-S-A" -> NASA).
"""
from __future__ import annotations

import re
from functools import lru_cache

_IRREGULAR = {"man": "men", "woman": "women", "child": "children", "person": "people", "mouse": "mice",
              "foot": "feet", "tooth": "teeth", "goose": "geese", "life": "lives", "wife": "wives",
              "knife": "knives", "leaf": "leaves", "wolf": "wolves", "half": "halves", "thief": "thieves"}
_ADJ_SUFFIX = ("ic", "ous", "ful", "less")
_ABBREV = {"doctor": ("dr",), "mister": ("mr",)}

_ONES = ["zero", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine", "ten", "eleven",
         "twelve", "thirteen", "fourteen", "fifteen", "sixteen", "seventeen", "eighteen", "nineteen"]
_TENS = ["", "", "twenty", "thirty", "forty", "fifty", "sixty", "seventy", "eighty", "ninety"]
_ORD_IRREG = {"one": "first", "two": "second", "three": "third", "five": "fifth", "eight": "eighth",
              "nine": "ninth", "twelve": "twelfth"}
UNITS = {"hundred", "thousand", "million", "billion", "trillion"}
_NUMBER_WORDS = set(_ONES) | set(_TENS[2:]) | UNITS | {"and"}


def cardinal_words(n: int) -> list[str]:
    if n < 20:
        return [_ONES[n]]
    if n < 100:
        t, o = divmod(n, 10)
        return [_TENS[t]] + ([_ONES[o]] if o else [])
    if n < 1000:
        h, r = divmod(n, 100)
        return [_ONES[h], "hundred"] + (cardinal_words(r) if r else [])
    if n < 1_000_000:
        th, r = divmod(n, 1000)
        return cardinal_words(th) + ["thousand"] + (cardinal_words(r) if r else [])
    raise ValueError("numbers >= 1,000,000 not supported")


def ordinal_word(w: str) -> str:
    if w in _ORD_IRREG:
        return _ORD_IRREG[w]
    if w.endswith("y"):
        return w[:-1] + "ieth"
    return w + "th"


def _suffix(n: int) -> str:
    if 10 <= n % 100 <= 20:
        return "th"
    return {1: "st", 2: "nd", 3: "rd"}.get(n % 10, "th")


def plural_forms(w: str) -> set[str]:
    """The word itself plus its plural/possessive surface forms (lower case)."""
    forms = {w}
    if not w.endswith(_ADJ_SUFFIX):
        if w in _IRREGULAR:
            forms.add(_IRREGULAR[w])
        if re.search(r"(s|x|z|ch|sh)$", w):
            forms.add(w + "es")
        elif re.search(r"[^aeiou]y$", w):
            forms.add(w[:-1] + "ies")
        else:
            forms.add(w + "s")
            if w.endswith("o"):
                forms.add(w + "es")
    for f in list(forms):
        forms.add(f + "'" if f.endswith("s") else f + "'s")
        forms.add(f + "'s")
    return forms


def _normalize(text: str) -> str:
    t = text.lower().replace("’", "'").replace("‘", "'").replace("–", "-").replace("—", " ")
    # letter-by-letter spellings: "n-a-s-a" / "u.s." -> "nasa" / "us"
    t = re.sub(r"\b(?:[a-z][.\-]){1,}[a-z]\b\.?", lambda m: re.sub(r"[.\-]", "", m.group(0)), t)
    t = re.sub(r"(\d),(\d{3})", r"\1\2", t)  # 1,000 -> 1000
    return t


def tokenize(text: str) -> list[str]:
    """Tokens split on spaces, hyphens and punctuation; apostrophes kept for possessives."""
    return [tok.strip("'") if not tok.endswith("s'") else tok
            for tok in re.findall(r"[a-z0-9]+(?:'[a-z0-9]*)?", _normalize(text))]


def _is_number_word(tok: str) -> bool:
    return tok in _NUMBER_WORDS or tok.isdigit()


@lru_cache(maxsize=4096)
def _alternatives(spec: str) -> tuple[tuple[frozenset, ...], ...]:
    """Each alternative phrase -> sequence of allowed token sets (one per position)."""
    alts = []
    for alt in [a.strip() for a in spec.split("/") if a.strip()]:
        for variant in _phrase_variants(alt):
            alts.append(variant)
    return tuple(alts)


def _phrase_variants(alt: str) -> list[tuple[frozenset, ...]]:
    toks = tokenize(alt)
    if not toks:
        return []
    has_number = any(t.isdigit() or t in _NUMBER_WORDS - {"and"} for t in toks)
    allow_ordinal = has_number and (len(toks) > 1 or toks[0].isdigit())
    variants: list[list[set]] = [[]]
    for i, tok in enumerate(toks):
        last = i == len(toks) - 1
        options: list[list[set]] = []
        if tok.isdigit():
            n = int(tok)
            words = cardinal_words(n) if n < 1_000_000 else [tok]
            digit_opt = {tok} | ({tok + _suffix(n)} if allow_ordinal else set())
            options.append([digit_opt])
            seq = [{w} for w in words]
            if allow_ordinal:
                seq[-1] = seq[-1] | {ordinal_word(words[-1])}
            options.append(seq)
            if len(tok) >= 3:  # "410" -> "four one zero" / "four ten"
                options.append([{_ONES[int(d)]} for d in tok])
                head, tail = int(tok[:-2]), int(tok[-2:])
                if 0 < head < 100 and tail >= 10:
                    options.append([{w} for w in cardinal_words(head)] + [{w} for w in cardinal_words(tail)])
        elif tok in _ONES or tok in _TENS[2:]:
            n = _ONES.index(tok) if tok in _ONES else _TENS.index(tok) * 10
            s = {tok, str(n)}
            if allow_ordinal:
                s |= {ordinal_word(tok), str(n) + _suffix(n)}
            if last:
                s |= {f + x for f in (tok, ordinal_word(tok)) for x in ("s", "'s")} if allow_ordinal else set()
            options.append([s])
        else:
            s = plural_forms(tok) if last else {tok}
            for full, abbrs in _ABBREV.items():
                if tok == full:
                    s |= set(abbrs)
            options.append([s])
        variants = [v + opt for v in variants for opt in options]
    return [tuple(frozenset(x) for x in v) for v in variants]


def _number_context_ok(tokens: list[str], start: int, end: int, phrase_len: int, target_is_unit: bool) -> bool:
    """A number target must not be part of a larger spoken number ("five hundred" != "five")."""
    if target_is_unit:
        return True
    first, last = tokens[start], tokens[end - 1]
    if not (_is_number_word(first) or _is_number_word(last)):
        return True
    before = tokens[start - 1] if start > 0 else ""
    after = tokens[end] if end < len(tokens) else ""
    if after in UNITS or (after.isdigit() and last.isdigit()):
        return False
    if before in _NUMBER_WORDS - {"and"} or (before.isdigit() and first.isdigit()):
        return False
    if after in _ONES[1:10] and last in _TENS:
        return False
    return True


def count_matches(spec: str, text: str) -> int:
    tokens = tokenize(text)
    n = 0
    spec_tokens = set(tokenize(spec))
    target_is_unit = bool(spec_tokens) and spec_tokens <= UNITS
    for variant in _alternatives(spec):
        L = len(variant)
        i = 0
        while i <= len(tokens) - L:
            if all(tokens[i + k] in variant[k] for k in range(L)) and \
                    _number_context_ok(tokens, i, i + L, L, target_is_unit):
                n += 1
                i += L
            else:
                i += 1
    return n


def said(spec: str, text: str) -> bool:
    return count_matches(spec, text) > 0
