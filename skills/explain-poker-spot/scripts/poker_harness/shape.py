"""Preflop range shape and borderlines.

How a coach explains a preflop node:

1. **Global shape**: what the whole range does, action by action, written as
   compact ranges per hand family ("Jam 12.9%: 44+, A7s+, A5s, ATo+ ...").
2. **Borderlines**: inside each family, the best and worst hand taking each
   action, and what the hands just above and just below do instead
   ("calls ATs-A8s; above it AJs 3-bets 48%; below it A7s folds").

Strategy rows come from GTO Wizard (class rows such as ``A5s``). If the
capture lists only the hands that don't fold, set ``hands_complete: true``
in the spot so unlisted classes count as the default action (fold).
"""

from __future__ import annotations

from dataclasses import dataclass, field

from .cards import RANKS, hand_class, parse_cards

MIXES = 15.0  # a secondary action at least this frequent is shown as a mix

# A hand "takes" the action it plays most often (its plurality action), so
# every class belongs to exactly one action and the borders are well defined.


def norm_class(hand: str) -> str | None:
    h = hand.strip()
    if len(h) == 4 and h[1] in "cdhs" and h[3] in "cdhs":
        return hand_class(parse_cards(h))
    if len(h) in (2, 3) and h[0].upper() in RANKS and h[1].upper() in RANKS:
        a, b = h[0].upper(), h[1].upper()
        if RANKS.index(b) > RANKS.index(a):
            a, b = b, a
        return a + b + h[2:].lower()
    return None


@dataclass
class Family:
    key: str
    name: str
    members: list[str]  # strongest first


def families() -> list[Family]:
    out = [Family("pairs", "Pocket pairs", [r * 2 for r in reversed(RANKS)])]
    names = {"A": "aces", "K": "kings", "Q": "queens", "J": "jacks", "T": "tens", "9": "nines", "8": "eights",
             "7": "sevens", "6": "sixes", "5": "fives", "4": "fours", "3": "threes"}
    for hi in reversed(RANKS[1:]):
        kickers = [k for k in reversed(RANKS[: RANKS.index(hi)])]
        for kind, word in (("s", "Suited"), ("o", "Offsuit")):
            out.append(Family(f"{hi}x{kind}", f"{word} {names[hi]} ({hi}x{kind})", [hi + k + kind for k in kickers]))
    return out


FAMILIES = families()


@dataclass
class Shape:
    actions: list[str]  # actions used (>= 1%), most frequent first
    fold_action: str | None
    strategy: dict[str, dict[str, float]]  # class -> action -> %
    ev: dict[str, dict[str, float]]
    complete: bool
    ranges: dict[str, str] = field(default_factory=dict)  # action -> compact range text
    borders: list[dict] = field(default_factory=list)


def build_shape(node_actions: dict[str, float], rows: list, complete: bool) -> Shape | None:
    if not node_actions or not rows:
        return None
    fold = next((a for a in node_actions if a.lower().startswith("fold")), None)
    strategy: dict[str, dict[str, float]] = {}
    ev: dict[str, dict[str, float]] = {}
    for r in rows:
        c = norm_class(r.hand)
        if c and r.strategy:
            strategy[c] = dict(r.strategy)
            if r.ev:
                ev[c] = dict(r.ev)
    if not strategy:
        return None
    used = [a for a, v in sorted(node_actions.items(), key=lambda kv: -kv[1]) if v >= 1.0]
    shape = Shape(used, fold, strategy, ev, complete)
    for act in used:
        if act == fold:
            continue
        shape.ranges[act] = compact_range(shape, act)
        shape.borders += borders_for(shape, act)
    return shape


def takes(shape: Shape, cls: str, act: str) -> bool | None:
    """True if ``act`` is this class's most frequent action (None if not captured)."""
    st = shape.strategy.get(cls)
    if st is None:
        if shape.complete and shape.fold_action:
            return act == shape.fold_action
        return None
    if not st:
        return None
    return max(st, key=st.get) == act


def freq(shape: Shape, cls: str, act: str) -> float | None:
    st = shape.strategy.get(cls)
    if st is None:
        if shape.complete and shape.fold_action:
            return 100.0 if act == shape.fold_action else 0.0
        return None
    return float(st.get(act, 0.0))


def main_other_action(shape: Shape, cls: str, exclude: str) -> str:
    st = shape.strategy.get(cls)
    if st is None:
        return shape.fold_action if (shape.complete and shape.fold_action) else "not captured"
    others = {a: v for a, v in st.items() if a != exclude}
    if not others:
        return "?"
    a, v = max(others.items(), key=lambda kv: kv[1])
    return f"{a} {v:.0f}%" if v < 99.5 else a


# ---------------------------------------------------------------------------
# Compact ranges
# ---------------------------------------------------------------------------

def _token_run(fam: Family, run: list[int]) -> str:
    m = fam.members
    first, last = m[run[0]], m[run[-1]]
    if len(run) == 1:
        return first
    if run[0] == 0:
        return f"{last}+"
    return f"{first}-{last}"


def compact_range(shape: Shape, act: str) -> str:
    parts: list[str] = []
    for fam in FAMILIES:
        flags = [freq(shape, c, act) for c in fam.members]
        mostly = [i for i, c in enumerate(fam.members) if takes(shape, c, act)]
        parts += [_token_run(fam, r) for r in _runs(mostly)]
        parts += [
            f"{fam.members[i]} ({f:.0f}%)"
            for i, f in enumerate(flags)
            if f is not None and f >= MIXES and i not in mostly
        ]
    return ", ".join(parts) if parts else "none"


# ---------------------------------------------------------------------------
# Borderlines
# ---------------------------------------------------------------------------

def _ev_note(shape: Shape, cls: str, act: str) -> str:
    e = shape.ev.get(cls)
    if not e or act not in e:
        return ""
    alt = {a: v for a, v in e.items() if a != act}
    if not alt:
        return ""
    best_alt, v = max(alt.items(), key=lambda kv: kv[1])
    return f"{act} {e[act]:+.2f} vs {best_alt} {v:+.2f}bb"


def borders_for(shape: Shape, act: str) -> list[dict]:
    """Per family: best and worst hand mostly taking ``act``, and the neighbours just outside."""
    rows = []
    for fam in FAMILIES:
        flags = [freq(shape, c, act) for c in fam.members]
        inside = [i for i, c in enumerate(fam.members) if takes(shape, c, act)]
        if not inside:
            continue
        top, bottom = inside[0], inside[-1]
        gaps = [fam.members[i] for i in range(top, bottom + 1) if i not in inside and flags[i] is not None]
        runs = _runs(inside)
        above = fam.members[top - 1] if top > 0 else None
        below = fam.members[bottom + 1] if bottom + 1 < len(fam.members) else None
        rows.append(
            {
                "action": act,
                "family": fam.name,
                "range": ", ".join(_token_run(fam, r) for r in runs),
                "split": len(runs) > 1,
                "freq_worst": flags[bottom],
                "best": fam.members[top],
                "worst": fam.members[bottom],
                "above": above,
                "above_does": main_other_action(shape, above, act) if above else None,
                "below": below,
                "below_does": main_other_action(shape, below, act) if below else None,
                "gaps": gaps,
                "gap_does": {g: main_other_action(shape, g, act) for g in gaps},
                "ev_worst": _ev_note(shape, fam.members[bottom], act),
                "ev_below": _ev_note(shape, below, act) if below else "",
            }
        )
    return rows


def _runs(idx: list[int]) -> list[list[int]]:
    runs: list[list[int]] = []
    for i in idx:
        if runs and i == runs[-1][-1] + 1:
            runs[-1].append(i)
        else:
            runs.append([i])
    return runs
