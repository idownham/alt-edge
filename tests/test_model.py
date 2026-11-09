"""M2: event types, base-rate model, look-ahead guard, indexed matcher, blend fit. Synthetic data only."""
import math
import random

import pytest

from bloodhound.backtest import blend_prob, fit_logistic
from bloodhound.event_types import classify
from bloodhound.matcher import count_matches, count_matches_indexed, token_index, tokenize
from bloodhound.model import Doc, HitTable, Params, cutoff_date, et_date, history, parse_word, predict, shrink

from test_matcher import COUNTS, DOES_NOT_COUNT


def doc(date, text, etype="remarks", seconds=1000, url=None):
    toks = tokenize(text)
    return Doc(url or f"u-{date}-{etype}", date, etype, seconds, toks, token_index(toks))


@pytest.mark.parametrize("word,text", COUNTS + DOES_NOT_COUNT + [
    ("Iran", "Iran Iran, Iran's oil"), ("five", "five hundred and five"), ("New York", "new york new york")])
def test_indexed_matcher_equals_reference(word, text):
    toks = tokenize(text)
    assert count_matches_indexed(word, toks, token_index(toks)) == count_matches(word, text)


def test_parse_word_thresholds():
    assert parse_word("Iran (3+ times)") == ("Iran", 3)
    assert parse_word("Tariff") == ("Tariff", 1)
    assert parse_word("401k / 401(k)") == ("401k / 401(k)", 1)


@pytest.mark.parametrize("title,etype", [
    ("his speech at the Macomb County Rally", "rally"),
    ("Telerally on April 20th", "rally"),
    ("Katie Pavlich Tonight Part 2 interview", "interview"),
    ("Fox Business: Kudlow", "interview"),
    ("Press Conference meeting with Benjamin Netanyahu on September 29th", "press_conference"),
    ("Cabinet Meeting", "press_conference"),
    ("Bilateral Meeting with the President of Ukraine", "bilateral"),
    ("Meeting at the White House With South Korean President Lee Jae Myung", "bilateral"),
    ("2026 State of the Union", "address"),
    ("Announcement in the Oval Office", "remarks"),
    (None, "remarks"),
    ("Roll Call Factba.se - Speech: Donald Trump Holds a Political Rally in Mount Pocono", "rally"),
    ("Roll Call Factba.se - Press Gaggle: Donald Trump Speaks to Reporters Before Air Force One", "press_conference"),
    ("Roll Call Factba.se - Interview: Brian Kilmeade Interviews Donald Trump", "interview"),
    ("Roll Call Factba.se - Remarks: Donald Trump Signs Executive Orders", "remarks"),
])
def test_event_type_rules(title, etype):
    assert classify(title) == etype


def test_shrink_is_beta_posterior_mean():
    p = Params(prior_strength=4.0, prior_mean=0.25)
    assert shrink(3, 4, p) == pytest.approx((3 + 1) / 8)
    assert shrink(0, 0, p) == pytest.approx(0.25)


def test_no_look_ahead_same_day_and_gap():
    docs = [doc("2026-01-01", "tariff"), doc("2026-01-02", "tariff"), doc("2026-01-03", "tariff"),
            doc("2026-01-05", "tariff")]
    p1 = Params(pool="all", last_n=10, min_seconds=0, gap_days=1)
    assert [d.date for d in history(docs, "2026-01-03", "remarks", p1)] == ["2026-01-02", "2026-01-01"]
    p2 = Params(pool="all", last_n=10, min_seconds=0, gap_days=2)
    assert [d.date for d in history(docs, "2026-01-03", "remarks", p2)] == ["2026-01-01"]
    assert cutoff_date("2026-03-01", 1) == "2026-02-28"


def test_pools_min_seconds_and_last_n():
    docs = [doc("2026-01-01", "oil", "rally"), doc("2026-01-02", "gas", "rally", seconds=100),
            doc("2026-01-03", "oil", "interview"), doc("2026-01-04", "gas", "rally")]
    p = Params(pool="same_type", last_n=10, min_seconds=300, prior_strength=0.0)
    prob, hits, n = predict(docs, "oil", "2026-02-01", "rally", p)
    assert (hits, n) == (1, 2) and prob == pytest.approx(0.5)
    p_all = Params(pool="all", last_n=2, min_seconds=0, prior_strength=0.0)
    assert predict(docs, "oil", "2026-02-01", "rally", p_all)[1:] == (1, 2)  # Jan 4 + Jan 3
    p_fb = Params(pool="same_type_fallback", last_n=10, min_seconds=0, prior_strength=0.0)
    assert predict(docs, "oil", "2026-02-01", "address", p_fb)[2] == 4  # no addresses -> all


def test_count_threshold_from_word():
    docs = [doc("2026-01-01", "Iran Iran"), doc("2026-01-02", "Iran Iran Iran")]
    p = Params(pool="all", last_n=10, min_seconds=0, prior_strength=0.0)
    assert predict(docs, "Iran (3+ times)", "2026-01-10", "remarks", p)[1:] == (1, 2)


def test_hit_table_matches_predict():
    rng = random.Random(1)
    words = ["oil", "tariff", "China", "Iran (2+ times)"]
    vocab = ["oil", "tariff", "china", "iran", "great", "very"]
    docs = [doc(f"2026-01-{d:02d}", " ".join(rng.choice(vocab) for _ in range(30)),
                rng.choice(["rally", "remarks"]), rng.choice([100, 500, 1200])) for d in range(1, 28)]
    markets = [{"ticker": f"T{i}", "word": w, "event_date": f"2026-01-{rng.randint(5, 28):02d}",
                "etype": rng.choice(["rally", "remarks", "address"])} for i, w in enumerate(words * 3)]
    pools = ("same_type", "all", "same_type_fallback")
    table = HitTable(docs, markets, 1, (0, 300), pools, max_n=10)
    for m in markets:
        for pool in pools:
            for ms in (0, 300):
                for n in (3, 10):
                    p = Params(pool, n, ms, 2.0, 0.4, 1)
                    assert table.prob(m["ticker"], p) == pytest.approx(
                        predict(docs, m["word"], m["event_date"], m["etype"], p)[0])


def test_et_date_crosses_midnight_utc():
    assert et_date("2026-01-10T02:30:00Z") == "2026-01-09"   # 21:30 ET the day before
    assert et_date("2026-07-10T03:59:00Z") == "2026-07-09"   # EDT


def test_fit_logistic_recovers_weights():
    rng = random.Random(7)
    true = [-0.5, 1.5, 0.7]
    X, y = [], []
    for _ in range(4000):
        x = [1.0, rng.gauss(0, 1), rng.gauss(0, 1)]
        p = 1 / (1 + math.exp(-sum(a * b for a, b in zip(true, x))))
        X.append(x)
        y.append(1 if rng.random() < p else 0)
    w = fit_logistic(X, y)
    for a, b in zip(w, true):
        assert a == pytest.approx(b, abs=0.15)


def test_blend_identity_returns_market():
    assert blend_prob([0.0, 1.0, 0.0], 0.3, 0.9) == pytest.approx(0.3)
