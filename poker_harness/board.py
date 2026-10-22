"""Board reading: texture, what beats the board, and range composition.

These are the facts a coach states before talking strategy ("all five cards
are spades, so only four cards beat the board"). Nothing here solves the
game; it classifies and counts combos you already have.
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
from typing import Iterable, Sequence

from .cards import (
    FLUSH,
    PAIR,
    RANKS,
    STRAIGHT,

    SUITS,
    TRIPS,
    TWO_PAIR,
    card_str,
    cards_str,
    category_of,
    describe_score,
    evaluate,
    hand_class,
    combo_str,
)
from .ranges import Range

SUIT_NAMES = {"c": "clubs", "d": "diamonds", "h": "hearts", "s": "spades"}

# ---------------------------------------------------------------------------
# Texture
# ---------------------------------------------------------------------------


@dataclass
class Texture:
    board: list[int]
    street: str
    suit_pattern: str  # rainbow / two-tone / monotone / four-flush / five-flush
    flush_suit: str | None
    flush_possible: bool
    flush_on_board: bool
    paired: bool
    trips_on_board: bool
    straight_possible: bool
    connected_ranks: int
    high_card: str
    board_hand: str | None  # river only: what the five board cards make
    notes: list[str] = field(default_factory=list)

    def summary(self) -> str:
        parts = [f"{cards_str(self.board, pretty=True, sep=' ')} ({self.street})", self.suit_pattern]
        if self.paired:
            parts.append("paired")
        if self.straight_possible:
            parts.append("straight possible")
        if self.board_hand:
            parts.append(f"board plays as {self.board_hand}")
        return ", ".join(parts)


STREETS = {3: "flop", 4: "turn", 5: "river"}


def texture(board: Sequence[int]) -> Texture:
    board = list(board)
    if len(board) not in STREETS:
        raise ValueError("Board must have 3, 4 or 5 cards")
    street = STREETS[len(board)]
    suit_counts = defaultdict(int)
    for c in board:
        suit_counts[SUITS[c % 4]] += 1
    top_suit, top_n = max(suit_counts.items(), key=lambda kv: kv[1])
    if top_n == 1:
        pattern = "rainbow"
    elif top_n == 2 and len(board) == 3:
        pattern = "two-tone"
    elif top_n == 2:
        pattern = "two-tone" if sum(1 for v in suit_counts.values() if v == 2) == 1 else "double two-tone"
    elif top_n == 3 and len(board) == 3:
        pattern = "monotone"
    elif top_n == 3:
        pattern = "three-flush"
    elif top_n == 4:
        pattern = "four-flush"
    else:
        pattern = "five-flush"
    ranks = [c // 4 for c in board]
    rank_counts = defaultdict(int)
    for r in ranks:
        rank_counts[r] += 1
    paired = any(v >= 2 for v in rank_counts.values())
    trips = any(v >= 3 for v in rank_counts.values())

    # Straight possible: some 5-rank window holds >= 3 board ranks.
    uniq = set(ranks)
    if 12 in uniq:
        uniq_w = uniq | {-1}
    else:
        uniq_w = uniq
    best_window = 0
    for low in range(-1, 9):
        n = sum(1 for r in range(low, low + 5) if r in uniq_w)
        best_window = max(best_window, n)
    straight_possible = best_window >= 3

    board_hand = describe_score(evaluate(board)) if len(board) == 5 else None
    t = Texture(
        board=board,
        street=street,
        suit_pattern=pattern,
        flush_suit=SUIT_NAMES[top_suit] if top_n >= 3 else None,
        flush_possible=top_n >= 3,
        flush_on_board=top_n == 5,
        paired=paired,
        trips_on_board=trips,
        straight_possible=straight_possible,
        connected_ranks=best_window,
        high_card=RANKS[max(ranks)],
        board_hand=board_hand,
    )
    if t.flush_on_board:
        t.notes.append(
            f"All five cards are {t.flush_suit}: everyone already has a flush, so the board itself is a {board_hand}."
        )
    elif top_n == 4:
        t.notes.append(f"Four {SUIT_NAMES[top_suit]} on board: any single {SUIT_NAMES[top_suit][:-1]} makes a flush.")
    elif top_n == 3 and street != "flop":
        t.notes.append(f"Three {SUIT_NAMES[top_suit]} on board: a flush needs two suited hole cards.")
    if paired:
        t.notes.append("Paired board: full houses and quads are possible.")
    return t


# ---------------------------------------------------------------------------
# What beats the board (river)
# ---------------------------------------------------------------------------


@dataclass
class BoardBeaters:
    board_score: int
    board_hand: str
    single_card_outs: list[int]  # cards that beat the board whatever the other hole card
    single_card_results: dict[int, str]
    two_card_only: list[str]  # classes that beat the board only with both cards

    def describe(self) -> str:
        if not self.single_card_outs and not self.two_card_only:
            return f"Nothing beats the board ({self.board_hand}); every hand chops."
        lines = [f"The board plays as {self.board_hand}."]
        if self.single_card_outs:
            lines.append(f"Single cards that beat it on their own: {self.outs_text()}.")
        return " ".join(lines)

    def grouped(self) -> dict[str, list[int]]:
        """Outs grouped by the hand they make (kicker upgrades share a group)."""
        groups: dict[str, list[int]] = {}
        for c in self.single_card_outs:
            res = self.single_card_results[c]
            # Same description as the board's hand means only the kicker improved.
            key = f"{res} with a better kicker" if res == self.board_hand else res
            groups.setdefault(key, []).append(c)
        return groups

    def outs_text(self) -> str:
        if len(self.single_card_outs) <= 6:
            return ", ".join(f"{card_str(c, True)} → {self.single_card_results[c]}" for c in self.single_card_outs)
        parts = []
        for res, cards in self.grouped().items():
            ranks = sorted({RANKS[c // 4] for c in cards}, key=RANKS.index, reverse=True)
            parts.append(f"{res}: {len(cards)} cards ({''.join(ranks)})")
        return "; ".join(parts)


def board_beaters(board: Sequence[int]) -> BoardBeaters:
    """On a 5-card board, which hole cards improve on the board's own hand."""
    board = list(board)
    if len(board) != 5:
        raise ValueError("board_beaters needs a river board")
    bscore = evaluate(board)
    rest = [c for c in range(52) if c not in board]
    single: list[int] = []
    results: dict[int, str] = {}
    for c in rest:
        worst = min(evaluate(board + [c, x]) for x in rest if x != c)
        if worst > bscore:
            single.append(c)
            results[c] = describe_score(worst)
    single.sort(reverse=True)
    # Classes that only improve with both cards (e.g. a pocket pair making a set).
    two_only: set[str] = set()
    for i, a in enumerate(rest):
        if a in single:
            continue
        for b in rest[i + 1 :]:
            if b in single:
                continue
            if evaluate(board + [a, b]) > bscore:
                two_only.add(hand_class((a, b)))
    return BoardBeaters(bscore, describe_score(bscore), single, results, sorted(two_only))


# ---------------------------------------------------------------------------
# Combo classification on a board
# ---------------------------------------------------------------------------

def classify_combo(combo: Sequence[int], board: Sequence[int]) -> dict:
    """Made-hand class plus simple draw flags, in coach language."""
    board = list(board)
    score = evaluate(list(combo) + board)
    cat = category_of(score)
    info: dict = {"score": score, "category": describe_score(score).split(",")[0].split(" of ")[0]}
    if len(board) == 5:
        info["plays_board"] = score == evaluate(board)
    else:
        info["plays_board"] = False

    board_ranks = sorted({c // 4 for c in board}, reverse=True)
    hole_ranks = sorted((c // 4 for c in combo), reverse=True)
    label = info["category"]
    if cat == PAIR:
        pair_rank = (score >> 16) & 0xF
        if hole_ranks[0] == hole_ranks[1] and pair_rank == hole_ranks[0]:
            if pair_rank > board_ranks[0]:
                label = "Overpair"
            else:
                label = "Underpair" if pair_rank < board_ranks[-1] else "Pocket pair below top card"
        elif pair_rank in board_ranks and pair_rank in hole_ranks:
            idx = board_ranks.index(pair_rank)
            label = ["Top pair", "Second pair", "Third pair"][idx] if idx < 3 else "Bottom pair"
        else:
            label = "Board pair only"
    elif cat == TRIPS:
        label = "Set" if hole_ranks[0] == hole_ranks[1] else "Trips"
    elif cat == TWO_PAIR:
        label = "Two pair"
    if info["plays_board"]:
        label = "Plays the board"
    info["label"] = label

    # Draws (flop/turn only)
    draws: list[str] = []
    if len(board) < 5 and cat < FLUSH:
        for s in range(4):
            suited = [c for c in list(combo) + board if c % 4 == s]
            hole_suited = [c for c in combo if c % 4 == s]
            if len(suited) == 4 and hole_suited:
                not_on_board = [r for r in range(12, -1, -1) if r * 4 + s not in board]
                nut = bool(not_on_board) and any(c // 4 == not_on_board[0] for c in hole_suited)
                draws.append("Nut flush draw" if nut else "Flush draw")
        if cat < STRAIGHT:
            outs = _straight_out_ranks(list(combo), board)
            if len(outs) >= 2:
                draws.append("Open-ended straight draw")
            elif len(outs) == 1:
                draws.append("Gutshot")
    info["draws"] = draws
    return info


def _rank_mask(ranks: Iterable[int]) -> int:
    m = 0
    for r in ranks:
        m |= 1 << r
    return m


def _straight_out_ranks(combo: list[int], board: list[int]) -> set[int]:
    """Ranks that would give hero a straight that the board alone doesn't make."""
    from .cards import _straight_high

    full = _rank_mask(c // 4 for c in combo + board)
    board_only = _rank_mask(c // 4 for c in board)
    if _straight_high(full) >= 0:
        return set()
    outs = set()
    for r in range(13):
        if full >> r & 1:
            continue
        if _straight_high(full | 1 << r) >= 0 and _straight_high(board_only | 1 << r) < 0:
            outs.add(r)
    return outs


# ---------------------------------------------------------------------------
# Range composition on a board
# ---------------------------------------------------------------------------

def composition(rng: Range, board: Sequence[int]) -> dict[str, dict]:
    """Group a range's combos by coach label: weight, share, examples."""
    board = list(board)
    live = rng.without(board)
    total = live.total() or 1.0
    groups: dict[str, dict] = {}
    for c, w in live.items():
        info = classify_combo(c, board)
        g = groups.setdefault(info["label"], {"combos": 0.0, "examples": [], "score_max": 0})
        g["combos"] += w
        g["score_max"] = max(g["score_max"], info["score"])
        if len(g["examples"]) < 6:
            g["examples"].append(combo_str(c))
        for d in info["draws"]:
            dg = groups.setdefault(f"+ {d}", {"combos": 0.0, "examples": [], "score_max": 0, "draw": True})
            dg["combos"] += w
            if len(dg["examples"]) < 6:
                dg["examples"].append(combo_str(c))
    for g in groups.values():
        g["pct"] = 100.0 * g["combos"] / total
    ordered = dict(
        sorted(groups.items(), key=lambda kv: (kv[1].get("draw", False), -kv[1]["score_max"]))
    )
    return ordered


def showdown_split(hero: Sequence[int], villain: Range, board: Sequence[int]) -> dict[str, float]:
    """River only: how much of villain's range hero beats, chops with, loses to."""
    board = list(board)
    if len(board) != 5:
        raise ValueError("showdown_split needs a river board")
    live = villain.without(board + list(hero))
    hs = evaluate(list(hero) + board)
    out = {"beats_hero": 0.0, "chops": 0.0, "hero_beats": 0.0}
    for c, w in live.items():
        vs = evaluate(list(c) + board)
        if vs > hs:
            out["beats_hero"] += w
        elif vs == hs:
            out["chops"] += w
        else:
            out["hero_beats"] += w
    out["total"] = sum(out.values())
    return out


def blocker_report(hero: Sequence[int], villain: Range, board: Sequence[int]) -> list[dict]:
    """How hero's two cards change villain's range, group by group."""
    board = list(board)
    before = composition(villain, board)
    after = composition(villain.without(list(hero)), board)
    rows = []
    for label, g in before.items():
        if g.get("draw"):
            continue
        a = after.get(label, {"combos": 0.0})["combos"]
        removed = g["combos"] - a
        rows.append(
            {
                "group": label,
                "before": round(g["combos"], 2),
                "after": round(a, 2),
                "removed_pct": round(100.0 * removed / g["combos"], 1) if g["combos"] else 0.0,
            }
        )
    return rows
