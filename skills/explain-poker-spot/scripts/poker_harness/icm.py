"""ICM helpers for explaining tournament decisions.

GTO Wizard already applies ICM when it solves. What it does not spell out is
*why* the strategy changed, so this module computes the quantities a coach
uses to explain it:

* ``icm_equities``  - each player's $EV (Malmuth-Harville model)
* ``bubble_factor`` - how much more a chip lost hurts than a chip won helps
* ``risk_premium``  - extra equity needed to call versus chip EV
* ``allin_call_requirements`` - chip-EV vs ICM break-even equity for a call

Stacks can be in any unit (chips or bb). Payouts are in any money unit and
are listed from 1st place down; places not listed pay nothing.
"""

from __future__ import annotations

import math
import random
from dataclasses import dataclass
from functools import lru_cache
from typing import Sequence

EXACT_LIMIT = 11  # exact Harville recursion up to this many players


def icm_equities(stacks: Sequence[float], payouts: Sequence[float], samples: int = 20000, seed: int = 7) -> list[float]:
    """Expected prize for each stack under the Malmuth-Harville model.

    Exact for up to ``EXACT_LIMIT`` live players; above that it samples
    finishing orders (Harville is a Plackett-Luce model, so ordering players
    by ``Exp(1)/stack`` draws an exact Harville finishing order).
    """
    stacks = [float(s) for s in stacks]
    pays = [float(p) for p in payouts]
    n = len(stacks)
    if n == 0:
        return []
    live = [i for i, s in enumerate(stacks) if s > 0]
    out = [0.0] * n
    if not live:
        return out
    # Busted players (stack 0) take the bottom places; with few live
    # players they would finish last, which pays nothing here.
    places = min(len(pays), len(live))
    if len(live) <= EXACT_LIMIT:
        res = _exact(tuple(stacks[i] for i in live), tuple(pays[:places]))
        for k, i in enumerate(live):
            out[i] = res[k]
        return out
    rng = random.Random(seed)
    acc = [0.0] * len(live)
    ls = [stacks[i] for i in live]
    for _ in range(samples):
        keys = [rng.expovariate(1.0) / s for s in ls]
        order = sorted(range(len(live)), key=keys.__getitem__)
        for place in range(places):
            acc[order[place]] += pays[place]
    for k, i in enumerate(live):
        out[i] = acc[k] / samples
    return out


def _exact(stacks: tuple[float, ...], pays: tuple[float, ...]) -> list[float]:
    n = len(stacks)

    @lru_cache(maxsize=None)
    def rec(mask: int) -> tuple[float, ...]:
        # mask = players still to be placed; place index = n - popcount(mask)
        place = n - bin(mask).count("1")
        if place >= len(pays) or mask == 0:
            return (0.0,) * n
        total = sum(stacks[i] for i in range(n) if mask >> i & 1)
        res = [0.0] * n
        for i in range(n):
            if not mask >> i & 1:
                continue
            p = stacks[i] / total
            sub = rec(mask & ~(1 << i))
            res[i] += p * pays[place]
            for j in range(n):
                res[j] += p * sub[j]
        return tuple(res)

    return list(rec((1 << n) - 1))


# ---------------------------------------------------------------------------
# Confrontations between two players
# ---------------------------------------------------------------------------


@dataclass
class AllInMath:
    """Break-even numbers for calling an all-in (or putting it in)."""

    hero: int
    villain: int
    risk: float  # chips hero puts at risk by calling
    pot_if_called: float
    ev_fold: float
    ev_win: float
    ev_lose: float
    chip_required: float  # break-even equity in chip EV (pot odds)
    icm_required: float  # break-even equity in $EV
    bubble_factor: float

    @property
    def risk_premium(self) -> float:
        return self.icm_required - self.chip_required


def allin_call_requirements(
    stacks: Sequence[float],
    payouts: Sequence[float],
    hero: int,
    villain: int,
    hero_committed: float = 0.0,
    villain_committed: float | None = None,
    dead_money: float = 0.0,
    samples: int = 20000,
) -> AllInMath:
    """Hero faces villain's all-in.

    ``stacks`` are the stacks at the start of the hand (before blinds/antes).
    ``hero_committed`` is what hero already has in the pot, ``villain_committed``
    defaults to villain's whole stack (he's all-in), and ``dead_money`` is
    everything else in the pot (other players' blinds and antes). Those
    players' stacks should already exclude it.
    """
    stacks = [float(s) for s in stacks]
    if villain_committed is None:
        villain_committed = stacks[villain]
    # Both players can only lose the smaller of the two amounts.
    eff = min(stacks[hero], villain_committed)
    hero_total = eff
    call_cost = hero_total - hero_committed
    villain_in = eff

    base = list(stacks)
    # Fold: hero loses what he committed; villain wins pot.
    fold = list(base)
    fold[hero] -= hero_committed
    fold[villain] += hero_committed + dead_money
    # Call and win: hero wins villain's matched chips and the dead money.
    win = list(base)
    win[hero] += eff + dead_money
    win[villain] -= eff
    # Call and lose.
    lose = list(base)
    lose[hero] -= hero_total
    lose[villain] += hero_total + dead_money
    eqs = [icm_equities(s, payouts, samples=samples) for s in (fold, win, lose)]
    ev_fold, ev_win, ev_lose = eqs[0][hero], eqs[1][hero], eqs[2][hero]

    pot_if_called = hero_committed + villain_in + dead_money + call_cost
    chip_req = call_cost / pot_if_called if pot_if_called else 0.0
    denom = ev_win - ev_lose
    icm_req = (ev_fold - ev_lose) / denom if denom > 0 else 1.0
    bf = bubble_factor(stacks, payouts, hero, villain, samples=samples)
    return AllInMath(hero, villain, call_cost, pot_if_called, ev_fold, ev_win, ev_lose, chip_req, icm_req, bf)


def bubble_factor(
    stacks: Sequence[float], payouts: Sequence[float], hero: int, villain: int, amount: float | None = None, samples: int = 20000
) -> float:
    """$ lost when hero loses ``amount`` to villain over $ gained when he wins it.

    Defaults to the effective stack between the two (a full double-up or bust
    confrontation). 1.0 means chips and money are worth the same; 1.5 means a
    lost chip costs 50% more than a won chip gains.
    """
    stacks = [float(s) for s in stacks]
    x = min(stacks[hero], stacks[villain]) if amount is None else amount
    now = icm_equities(stacks, payouts, samples=samples)[hero]
    win = list(stacks)
    win[hero] += x
    win[villain] -= x
    lose = list(stacks)
    lose[hero] -= x
    lose[villain] += x
    ev_win = icm_equities(win, payouts, samples=samples)[hero]
    ev_lose = icm_equities(lose, payouts, samples=samples)[hero]
    gain = ev_win - now
    loss = now - ev_lose
    if gain <= 0:
        return math.inf
    return loss / gain


def required_equity_from_bubble_factor(bf: float, pot_odds_risk: float, pot_odds_reward: float) -> float:
    """Break-even equity when losing costs ``bf`` times as much as winning gains.

    ``risk`` is what you put in, ``reward`` what you stand to win (pot before
    your call). Chip EV is the ``bf = 1`` case: risk / (risk + reward).
    """
    return bf * pot_odds_risk / (bf * pot_odds_risk + pot_odds_reward)


def pressure_table(stacks: Sequence[float], payouts: Sequence[float], names: Sequence[str], samples: int = 20000) -> list[list[float]]:
    """Bubble factor of every player (row) against every other (column)."""
    n = len(stacks)
    out = [[0.0] * n for _ in range(n)]
    for i in range(n):
        for j in range(n):
            if i == j or stacks[i] <= 0 or stacks[j] <= 0:
                continue
            out[i][j] = bubble_factor(stacks, payouts, i, j, samples=samples)
    return out


def pad_with_field(table_stacks: Sequence[float], players_left: int, average_stack: float) -> list[float]:
    """Approximate the rest of an MTT field as players with the average stack.

    For a big field you rarely know every stack. Padding the table with
    ``players_left - len(table)`` average stacks keeps the payout ladder
    realistic; the table players keep their own indices (0..len-1).
    """
    others = max(0, players_left - len(table_stacks))
    return list(table_stacks) + [float(average_stack)] * others


def describe_bubble_factor(bf: float) -> str:
    if bf == math.inf:
        return "winning chips gains nothing, so any risk is pure downside"
    if bf < 1.1:
        return "close to chip EV; ICM barely matters"
    if bf < 1.3:
        return "mild ICM pressure"
    if bf < 1.6:
        return "significant ICM pressure"
    return "heavy ICM pressure; calling off needs a big edge"
