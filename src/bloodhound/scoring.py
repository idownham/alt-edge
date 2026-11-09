"""Scoring per spec v2: market probability at T_ref, quote filter, Brier, log loss, reliability table,
event-clustered bootstrap. Prices and fees are Decimal; statistics over probabilities use float
(they are scores, not money)."""
from __future__ import annotations

import math
import random
from dataclasses import dataclass
from decimal import Decimal, ROUND_CEILING

MAX_SPREAD = Decimal("0.10")      # spec v2 / Q2: yes spread must be <= 10 cents
TAKER_COEF = Decimal("0.07")      # Q9, Ian checked kalshi.com/fee-schedule 2026-10-14
CENT = Decimal("0.01")
BOOTSTRAP_DRAWS = 10_000
BOOTSTRAP_SEED = 20261014         # fixed seed (criteria confirmed 2026-10-14)


def two_sided(yes_bid: Decimal | None, yes_ask: Decimal | None) -> bool:
    """A real quote on both sides: bid > 0 and ask < 1 (0 / 1 mean no orders on that side)."""
    return yes_bid is not None and yes_ask is not None and Decimal(0) < yes_bid <= yes_ask < Decimal(1)


def passes_quote_filter(yes_bid: Decimal | None, yes_ask: Decimal | None) -> bool:
    return two_sided(yes_bid, yes_ask) and (yes_ask - yes_bid) <= MAX_SPREAD


def market_prob(yes_bid: Decimal, yes_ask: Decimal) -> Decimal:
    """p_mkt = midpoint of yes_bid and yes_ask (spec v2)."""
    return (yes_bid + yes_ask) / 2


def taker_fee(contracts: int, price: Decimal) -> Decimal:
    """Kalshi quadratic taker fee: ceil_to_cent(0.07 * C * P * (1 - P)), in dollars."""
    if contracts < 0 or not (Decimal(0) <= price <= Decimal(1)):
        raise ValueError("bad contracts/price")
    raw = TAKER_COEF * contracts * price * (1 - price)
    return raw.quantize(CENT, rounding=ROUND_CEILING)


def brier(probs, outcomes) -> float:
    pairs = list(zip(probs, outcomes, strict=True))
    if not pairs:
        raise ValueError("no forecasts")
    return sum((float(p) - y) ** 2 for p, y in pairs) / len(pairs)


def log_loss(probs, outcomes, eps: float = 1e-6) -> float:
    pairs = list(zip(probs, outcomes, strict=True))
    tot = 0.0
    for p, y in pairs:
        p = min(max(float(p), eps), 1 - eps)
        tot -= y * math.log(p) + (1 - y) * math.log(1 - p)
    return tot / len(pairs)


def reliability_table(probs, outcomes, bins: int = 10) -> list[dict]:
    rows = [{"bin": f"{b / bins:.1f}-{(b + 1) / bins:.1f}", "n": 0, "mean_p": 0.0, "freq": 0.0}
            for b in range(bins)]
    for p, y in zip(probs, outcomes, strict=True):
        b = min(int(float(p) * bins), bins - 1)
        rows[b]["n"] += 1
        rows[b]["mean_p"] += float(p)
        rows[b]["freq"] += y
    for r in rows:
        if r["n"]:
            r["mean_p"] /= r["n"]
            r["freq"] /= r["n"]
    return rows


@dataclass
class BootstrapResult:
    diff: float          # model Brier - market Brier on the full sample
    lo95: float
    hi95: float
    draws: int
    n_events: int


def clustered_bootstrap_brier_diff(records, draws: int = BOOTSTRAP_DRAWS,
                                   seed: int = BOOTSTRAP_SEED) -> BootstrapResult:
    """records: iterable of (event_id, p_model, p_market, outcome 0/1).
    Resample EVENTS with replacement; each draw's statistic is the pooled market-level
    (model Brier - market Brier) over the resampled events' markets."""
    by_event: dict = {}
    for ev, pm, pk, y in records:
        se_m = (float(pm) - y) ** 2
        se_k = (float(pk) - y) ** 2
        acc = by_event.setdefault(ev, [0.0, 0])
        acc[0] += se_m - se_k
        acc[1] += 1
    events = list(by_event.values())
    if not events:
        raise ValueError("no records")
    total = sum(e[0] for e in events) / sum(e[1] for e in events)
    rng = random.Random(seed)
    k = len(events)
    stats = []
    for _ in range(draws):
        s = n = 0
        for _ in range(k):
            e = events[rng.randrange(k)]
            s += e[0]
            n += e[1]
        stats.append(s / n)
    stats.sort()
    lo = stats[int(0.025 * draws)]
    hi = stats[min(int(math.ceil(0.975 * draws)) - 1, draws - 1)]
    return BootstrapResult(total, lo, hi, draws, k)
