"""Cards, combos and a 5-7 card hand evaluator.

Cards are ints 0..51: ``rank = card // 4`` (0 = deuce ... 12 = ace) and
``suit = card % 4`` (0 = clubs, 1 = diamonds, 2 = hearts, 3 = spades).
The evaluator returns an integer score; a higher score is a better hand,
and equal scores are a split.
"""

from __future__ import annotations

from itertools import combinations
from typing import Iterable, Sequence

RANKS = "23456789TJQKA"
SUITS = "cdhs"
SUIT_SYMBOLS = {"c": "♣", "d": "♦", "h": "♥", "s": "♠"}

# Hand categories, weakest to strongest.
HIGH_CARD, PAIR, TWO_PAIR, TRIPS, STRAIGHT, FLUSH, FULL_HOUSE, QUADS, STRAIGHT_FLUSH = range(9)
CATEGORY_NAMES = [
    "High card",
    "Pair",
    "Two pair",
    "Three of a kind",
    "Straight",
    "Flush",
    "Full house",
    "Four of a kind",
    "Straight flush",
]

DECK = tuple(range(52))


def card(text: str) -> int:
    """Parse a card such as ``'As'`` or ``'td'`` into an int."""
    text = text.strip()
    if len(text) != 2:
        raise ValueError(f"Bad card {text!r}")
    r = RANKS.find(text[0].upper())
    s = SUITS.find(text[1].lower())
    if r < 0 or s < 0:
        raise ValueError(f"Bad card {text!r}")
    return r * 4 + s


def parse_cards(text: str | Iterable[str] | Iterable[int]) -> list[int]:
    """Parse ``'KsJs6s'``, ``'Ks Js 6s'``, ``['Ks', 'Js']`` or ints."""
    if isinstance(text, str):
        compact = text.replace(" ", "").replace(",", "")
        if len(compact) % 2:
            raise ValueError(f"Bad card string {text!r}")
        cards = [card(compact[i : i + 2]) for i in range(0, len(compact), 2)]
    else:
        cards = [c if isinstance(c, int) else card(c) for c in text]
    if len(set(cards)) != len(cards):
        raise ValueError(f"Duplicate card in {text!r}")
    return cards


def card_str(c: int, pretty: bool = False) -> str:
    s = SUITS[c % 4]
    return RANKS[c // 4] + (SUIT_SYMBOLS[s] if pretty else s)


def cards_str(cards: Iterable[int], pretty: bool = False, sep: str = "") -> str:
    return sep.join(card_str(c, pretty) for c in cards)


def rank_of(c: int) -> int:
    return c // 4


def suit_of(c: int) -> int:
    return c % 4


# ---------------------------------------------------------------------------
# Evaluator
# ---------------------------------------------------------------------------

def _pack(category: int, kickers: Sequence[int]) -> int:
    score = category
    for i in range(5):
        score = score * 16 + (kickers[i] if i < len(kickers) else 0)
    return score


def _straight_high(rank_mask: int) -> int:
    """Highest straight top-rank in a 13-bit rank mask, or -1."""
    for top in range(12, 3, -1):
        need = 0b11111 << (top - 4)
        if rank_mask & need == need:
            return top
    # Wheel: A-2-3-4-5 (ace is bit 12)
    if rank_mask & 0b1000000001111 == 0b1000000001111:
        return 3
    return -1


def evaluate(cards: Sequence[int]) -> int:
    """Score the best five-card hand from 5-7 cards."""
    rank_counts = [0] * 13
    suit_cards: list[list[int]] = [[], [], [], []]
    for c in cards:
        r = c >> 2
        rank_counts[r] += 1
        suit_cards[c & 3].append(r)

    # Flush / straight flush
    for ranks in suit_cards:
        if len(ranks) >= 5:
            fmask = 0
            for r in ranks:
                fmask |= 1 << r
            sf = _straight_high(fmask)
            if sf >= 0:
                return _pack(STRAIGHT_FLUSH, [sf])
            best = sorted(ranks, reverse=True)[:5]
            flush_score = _pack(FLUSH, best)
            break
    else:
        flush_score = -1

    quads = trips = -1
    pairs: list[int] = []
    singles: list[int] = []
    for r in range(12, -1, -1):
        n = rank_counts[r]
        if n == 4:
            quads = r
        elif n == 3:
            if trips < 0:
                trips = r
            else:
                pairs.append(r)  # second set of trips plays as a pair
        elif n == 2:
            pairs.append(r)
        elif n == 1:
            singles.append(r)

    if quads >= 0:
        kick = max([r for r in range(13) if rank_counts[r] and r != quads], default=0)
        return _pack(QUADS, [quads, kick])
    if trips >= 0 and pairs:
        return _pack(FULL_HOUSE, [trips, max(pairs)])
    if flush_score >= 0:
        return flush_score

    rmask = 0
    for r in range(13):
        if rank_counts[r]:
            rmask |= 1 << r
    st = _straight_high(rmask)
    if st >= 0:
        return _pack(STRAIGHT, [st])
    if trips >= 0:
        return _pack(TRIPS, [trips] + singles[:2])
    if len(pairs) >= 2:
        p1, p2 = pairs[0], pairs[1]
        rest = sorted([r for r in range(13) if rank_counts[r] and r not in (p1, p2)], reverse=True)
        return _pack(TWO_PAIR, [p1, p2, rest[0] if rest else 0])
    if pairs:
        return _pack(PAIR, [pairs[0]] + singles[:3])
    return _pack(HIGH_CARD, singles[:5])


def category_of(score: int) -> int:
    return score >> 20


def category_name(score: int) -> str:
    return CATEGORY_NAMES[category_of(score)]


def describe_score(score: int) -> str:
    """Human readable, e.g. 'Flush, K-high' or 'Straight flush, K-high'."""
    cat = category_of(score)
    k = [(score >> (4 * (4 - i))) & 0xF for i in range(5)]
    hi = RANKS[k[0]]
    if cat in (STRAIGHT, STRAIGHT_FLUSH):
        return f"{CATEGORY_NAMES[cat]}, {hi}-high"
    if cat == FLUSH:
        return f"Flush, {'-'.join(RANKS[x] for x in k)}"
    if cat == FULL_HOUSE:
        return f"Full house, {RANKS[k[0]]}s full of {RANKS[k[1]]}s"
    if cat in (QUADS, TRIPS):
        return f"{CATEGORY_NAMES[cat]}, {RANKS[k[0]]}s"
    if cat == TWO_PAIR:
        return f"Two pair, {RANKS[k[0]]}s and {RANKS[k[1]]}s"
    if cat == PAIR:
        return f"Pair of {RANKS[k[0]]}s"
    return f"High card, {hi}"


# ---------------------------------------------------------------------------
# Combos and hand classes
# ---------------------------------------------------------------------------

Combo = tuple  # (high_card, low_card) as ints, high card first


def make_combo(a: int, b: int) -> tuple[int, int]:
    if a == b:
        raise ValueError("A combo needs two different cards")
    return (a, b) if a > b else (b, a)


def combo_str(combo: Sequence[int], pretty: bool = False) -> str:
    return cards_str(combo, pretty)


def parse_combo(text: str) -> tuple[int, int]:
    cs = parse_cards(text)
    if len(cs) != 2:
        raise ValueError(f"A combo is two cards, got {text!r}")
    return make_combo(cs[0], cs[1])


def hand_class(combo: Sequence[int]) -> str:
    """'AKs', 'AKo' or 'QQ' for a combo."""
    a, b = combo
    ra, rb = a >> 2, b >> 2
    if ra < rb:
        ra, rb = rb, ra
        a, b = b, a
    if ra == rb:
        return RANKS[ra] * 2
    return RANKS[ra] + RANKS[rb] + ("s" if (a & 3) == (b & 3) else "o")


ALL_COMBOS: tuple[tuple[int, int], ...] = tuple(make_combo(a, b) for a, b in combinations(range(52), 2))


def all_hand_classes() -> list[str]:
    """The 169 starting-hand classes in grid order (AA, AKs, ... 22)."""
    out = []
    for i in range(12, -1, -1):
        for j in range(12, -1, -1):
            if i == j:
                out.append(RANKS[i] * 2)
            elif j < i:
                out.append(RANKS[i] + RANKS[j] + "s")
            else:
                out.append(RANKS[j] + RANKS[i] + "o")
    return out


def class_combos(cls: str) -> list[tuple[int, int]]:
    """All combos of a class such as 'AKs', 'AKo', 'AK' or 'TT'."""
    cls = cls.strip()
    r1 = RANKS.index(cls[0].upper())
    r2 = RANKS.index(cls[1].upper())
    kind = cls[2].lower() if len(cls) > 2 else ""
    out = []
    if r1 == r2:
        for s1, s2 in combinations(range(4), 2):
            out.append(make_combo(r1 * 4 + s1, r2 * 4 + s2))
        return out
    for s1 in range(4):
        for s2 in range(4):
            if kind == "s" and s1 != s2:
                continue
            if kind == "o" and s1 == s2:
                continue
            out.append(make_combo(r1 * 4 + s1, r2 * 4 + s2))
    return out


def class_combo_count(cls: str) -> int:
    if cls[0] == cls[1]:
        return 6
    return 4 if cls.endswith("s") else 12


def conflicts(combo: Sequence[int], dead: Iterable[int]) -> bool:
    dead = set(dead)
    return combo[0] in dead or combo[1] in dead
