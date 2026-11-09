from decimal import Decimal as D

import pytest

from bloodhound.scoring import (brier, clustered_bootstrap_brier_diff, log_loss, market_prob,
                                passes_quote_filter, reliability_table, taker_fee, two_sided)


def test_market_prob_is_decimal_midpoint():
    p = market_prob(D("0.54"), D("0.59"))
    assert p == D("0.565") and isinstance(p, D)


@pytest.mark.parametrize("bid,ask,ok", [
    (D("0.54"), D("0.59"), True),
    (D("0.40"), D("0.50"), True),     # exactly 10c spread is allowed
    (D("0.40"), D("0.51"), False),    # 11c
    (D("0"), D("0.05"), False),       # no bid
    (D("0.95"), D("1"), False),       # no ask
    (None, D("0.5"), False),
    (D("0.6"), D("0.5"), False),      # crossed
])
def test_quote_filter(bid, ask, ok):
    assert passes_quote_filter(bid, ask) is ok


def test_two_sided_needs_both():
    assert two_sided(D("0.01"), D("0.99"))
    assert not two_sided(D("0.01"), None)


@pytest.mark.parametrize("c,p,fee", [
    (1, D("0.50"), D("0.02")),    # 0.0175 -> ceil 0.02
    (5, D("0.50"), D("0.09")),    # 0.0875 -> 0.09
    (1, D("0.10"), D("0.01")),    # 0.0063 -> 0.01
    (5, D("0.10"), D("0.04")),    # 0.0315 -> 0.04
    (100, D("0.50"), D("1.75")),  # exact, no rounding
    (5, D("0"), D("0.00")),
    (5, D("1"), D("0.00")),
])
def test_taker_fee_ceil_to_cent(c, p, fee):
    out = taker_fee(c, p)
    assert out == fee and isinstance(out, D)


def test_taker_fee_rejects_bad_input():
    with pytest.raises(ValueError):
        taker_fee(1, D("1.2"))


def test_brier_and_logloss():
    assert brier([1, 0, 0.5], [1, 0, 1]) == pytest.approx(0.25 / 3)
    assert brier([D("0.7")], [1]) == pytest.approx(0.09)
    assert log_loss([0.5, 0.5], [1, 0]) == pytest.approx(0.693147, rel=1e-5)
    with pytest.raises(ValueError):
        brier([0.5], [1, 0])


def test_reliability_table_bins():
    rows = reliability_table([0.05, 0.15, 0.95, 1.0], [0, 1, 1, 1])
    assert rows[0]["n"] == 1 and rows[1]["freq"] == 1.0
    assert rows[9]["n"] == 2 and rows[9]["mean_p"] == pytest.approx(0.975)


def test_bootstrap_detects_clear_win_and_is_reproducible():
    recs = []
    for ev in range(40):
        for k in range(10):
            y = (ev + k) % 2
            recs.append((ev, 0.8 if y else 0.2, 0.5, y))  # model always better
    r1 = clustered_bootstrap_brier_diff(recs, draws=2000)
    r2 = clustered_bootstrap_brier_diff(recs, draws=2000)
    assert r1 == r2
    assert r1.diff == pytest.approx(0.04 - 0.25)
    assert r1.hi95 < 0 and r1.n_events == 40


def test_bootstrap_equal_forecasts_ci_straddles_zero_or_zero():
    recs = [(ev, 0.5, 0.5, ev % 2) for ev in range(30)]
    r = clustered_bootstrap_brier_diff(recs, draws=500)
    assert r.diff == 0 and r.lo95 == 0 and r.hi95 == 0


def test_bootstrap_resamples_events_not_markets():
    # One event with many markets where model is worse dominates the uncertainty.
    recs = [(0, 0.9, 0.1, 0)] * 50 + [(ev, 0.6, 0.5, 1) for ev in range(1, 6)]
    r = clustered_bootstrap_brier_diff(recs, draws=2000)
    assert r.n_events == 6
    assert r.lo95 < r.diff < r.hi95 or r.lo95 <= r.diff <= r.hi95
