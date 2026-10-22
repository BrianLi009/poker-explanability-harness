"""Weighted ranges as you read them off GTO Wizard.

A range maps each two-card combo to a weight between 0 and 1 (GTO Wizard's
"Range" column). Ranges can be written as text::

    "AA, KK:0.5, AKs, A5s-A2s, 22+, KTo+, AsKh:0.22"

or as a dict ``{"AsKh": 0.22, "QQ": 1, "T9s": 0.68}`` where keys are combos
or hand classes. The harness never solves for a range; it only counts and
groups the combos you give it.
"""

from __future__ import annotations

from collections import defaultdict
from typing import Iterable, Mapping

from .cards import (
    RANKS,
    class_combos,
    combo_str,
    hand_class,
    make_combo,
    parse_cards,
)

Combo = tuple[int, int]


class Range:
    """A mapping combo -> weight with card-removal helpers."""

    def __init__(self, weights: Mapping[Combo, float] | None = None):
        self.weights: dict[Combo, float] = {}
        for c, w in (weights or {}).items():
            if w > 0:
                self.weights[c] = float(w)

    # -- construction -----------------------------------------------------
    @classmethod
    def parse(cls, spec: "str | Mapping[str, float] | Range | None") -> "Range":
        if spec is None:
            return cls()
        if isinstance(spec, Range):
            return spec
        if isinstance(spec, Mapping):
            out: dict[Combo, float] = {}
            for key, w in spec.items():
                for c in _expand_token(key):
                    out[c] = float(w)
            return cls(out)
        out = {}
        for raw in spec.replace("\n", ",").split(","):
            raw = raw.strip()
            if not raw:
                continue
            weight = 1.0
            if ":" in raw:
                raw, w = raw.split(":", 1)
                weight = float(w)
            for c in _expand_token(raw.strip()):
                out[c] = weight
        return cls(out)

    # -- queries ----------------------------------------------------------
    def without(self, dead: Iterable[int]) -> "Range":
        dead = set(dead)
        return Range({c: w for c, w in self.weights.items() if c[0] not in dead and c[1] not in dead})

    def total(self) -> float:
        return sum(self.weights.values())

    def __len__(self) -> int:
        return len(self.weights)

    def items(self):
        return self.weights.items()

    def by_class(self) -> dict[str, float]:
        out: dict[str, float] = defaultdict(float)
        for c, w in self.weights.items():
            out[hand_class(c)] += w
        return dict(out)

    def percent_of_hands(self) -> float:
        """Share of all 1326 starting combos (preflop range width)."""
        return 100.0 * self.total() / 1326.0

    def combos_containing(self, card: int) -> float:
        return sum(w for c, w in self.weights.items() if card in c)

    def to_dict(self) -> dict[str, float]:
        return {combo_str(c): round(w, 4) for c, w in sorted(self.weights.items(), reverse=True)}


# ---------------------------------------------------------------------------
# Token expansion
# ---------------------------------------------------------------------------

def _expand_token(tok: str) -> list[Combo]:
    tok = tok.strip()
    if not tok:
        return []
    # Exact combo like "AsKh"
    if len(tok) == 4 and tok[1].lower() in "cdhs" and tok[3].lower() in "cdhs":
        a, b = parse_cards(tok)
        return [make_combo(a, b)]
    if "-" in tok:
        lo_hi = tok.split("-")
        return _expand_dash(lo_hi[0].strip(), lo_hi[1].strip())
    if tok.endswith("+"):
        return _expand_plus(tok[:-1])
    return class_combos(_norm(tok))


def _norm(tok: str) -> str:
    t = tok[0].upper() + tok[1].upper() + tok[2:].lower()
    r1, r2 = RANKS.index(t[0]), RANKS.index(t[1])
    if r2 > r1:
        t = t[1] + t[0] + t[2:]
    return t


def _expand_plus(tok: str) -> list[Combo]:
    t = _norm(tok)
    r1, r2 = RANKS.index(t[0]), RANKS.index(t[1])
    kind = t[2:] if len(t) > 2 else ""
    out: list[Combo] = []
    if r1 == r2:  # 77+ -> 77..AA
        for r in range(r1, 13):
            out += class_combos(RANKS[r] * 2)
        return out
    # A2s+ -> A2s..AKs (kicker climbs up to just below the top card)
    for k in range(r2, r1):
        out += class_combos(RANKS[r1] + RANKS[k] + kind)
    return out


def _expand_dash(a: str, b: str) -> list[Combo]:
    ta, tb = _norm(a), _norm(b)
    ra1, ra2 = RANKS.index(ta[0]), RANKS.index(ta[1])
    rb1, rb2 = RANKS.index(tb[0]), RANKS.index(tb[1])
    kind = ta[2:] if len(ta) > 2 else ""
    out: list[Combo] = []
    if ra1 == ra2 and rb1 == rb2:  # 99-55
        for r in range(min(ra1, rb1), max(ra1, rb1) + 1):
            out += class_combos(RANKS[r] * 2)
        return out
    if ra1 == rb1:  # A9s-A2s
        for k in range(min(ra2, rb2), max(ra2, rb2) + 1):
            out += class_combos(RANKS[ra1] + RANKS[k] + kind)
        return out
    gap = ra1 - ra2
    if rb1 - rb2 == gap:  # T9s-65s
        for top in range(min(ra1, rb1), max(ra1, rb1) + 1):
            out += class_combos(RANKS[top] + RANKS[top - gap] + kind)
        return out
    raise ValueError(f"Can't expand range {a}-{b}")
