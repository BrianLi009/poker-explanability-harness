"""The spot: everything you read off GTO Wizard for one decision.

A spot is plain JSON (see ``docs/spot-schema.md``). This module loads it,
normalises frequencies (GTO Wizard shows percentages; 0.545 and 54.5 are both
accepted) and gives the explanation builders typed access.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .cards import parse_cards
from .ranges import Range


def to_pct(value: float | None) -> float | None:
    if value is None:
        return None
    return float(value)


def normalise_actions(actions: dict[str, float] | None) -> dict[str, float]:
    """Return action -> percent (0-100)."""
    if not actions:
        return {}
    vals = [float(v) for v in actions.values()]
    scale = 100.0 if all(v <= 1.0 for v in vals) and sum(vals) <= 1.02 else 1.0
    return {k: float(v) * scale for k, v in actions.items()}


def normalise_freq_list(freqs: list[float]) -> list[float]:
    """Street frequencies as fractions 0-1 (accepts percents)."""
    out = []
    for f in freqs:
        f = float(f)
        out.append(f / 100.0 if f > 1.0 else f)
    return out


@dataclass
class HandRow:
    hand: str
    strategy: dict[str, float] = field(default_factory=dict)
    ev: dict[str, float] = field(default_factory=dict)
    weight: float | None = None
    equity: float | None = None
    label: str | None = None
    ev_best: float | None = None  # GTO Wizard Summary "EV" column: the hand's EV at its solver mix
    extra: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, d: dict) -> "HandRow":
        known = {"hand", "strategy", "ev", "weight", "equity", "label", "ev_best"}
        return cls(
            hand=str(d["hand"]),
            strategy=normalise_actions(d.get("strategy")),
            ev={k: float(v) for k, v in (d.get("ev") or {}).items()},
            weight=d.get("weight"),
            equity=d.get("equity"),
            label=d.get("label"),
            ev_best=d.get("ev_best"),
            extra={k: v for k, v in d.items() if k not in known},
        )

    def best_action(self) -> str | None:
        if self.ev:
            return max(self.ev, key=self.ev.get)
        if self.strategy:
            return max(self.strategy, key=self.strategy.get)
        return None


@dataclass
class Node:
    player: str
    actions: dict[str, float]
    combos: dict[str, float] = field(default_factory=dict)
    facing: str | None = None
    pot_odds: float | None = None
    hands: list[HandRow] = field(default_factory=list)
    breakdown: list[dict] = field(default_factory=list)
    note: str | None = None

    @classmethod
    def from_dict(cls, d: dict | None) -> "Node | None":
        if not d:
            return None
        return cls(
            player=str(d.get("player", "?")),
            actions=normalise_actions(d.get("actions")),
            combos={k: float(v) for k, v in (d.get("combos") or {}).items()},
            facing=d.get("facing"),
            pot_odds=d.get("pot_odds"),
            hands=[HandRow.from_dict(h) for h in d.get("hands", [])],
            breakdown=list(d.get("breakdown", [])),
            note=d.get("note"),
        )


class Spot:
    def __init__(self, data: dict):
        self.data = data
        self.module: str = data.get("module", "postflop")
        self.title: str = data.get("title", "Hand explanation")
        self.source: str | None = data.get("source")
        self.format: dict = data.get("format", {})
        self.table: list[dict] = data.get("table", [])
        self.hero: str = data.get("hero", "Hero")
        self.villain: str = data.get("villain", "Villain")
        self.history: list[dict] = data.get("history", [])
        self.board = parse_cards(data["board"]) if data.get("board") else []
        self.pot: float | None = data.get("pot")
        self.stacks_behind: dict[str, float] = data.get("stacks_behind", {})
        self.node = Node.from_dict(data.get("node"))
        hh = data.get("hero_hand")
        self.hero_hand: HandRow | None = HandRow.from_dict(hh) if hh else None
        self.hands: list[HandRow] = [HandRow.from_dict(h) for h in data.get("hands", [])]
        self.ranges: dict[str, Range] = {k: Range.parse(v) for k, v in (data.get("ranges") or {}).items()}
        # Ranges that only list part of the real range (e.g. just the strong combos).
        self.partial_ranges: set[str] = set(data.get("ranges_partial", []))
        self.breakdown: dict[str, list[dict]] = data.get("breakdown", {})
        self.equity: dict[str, dict] = data.get("equity", {})
        self.response = Node.from_dict(data.get("response"))
        self.alternatives: list[dict] = data.get("alternatives", [])
        self.rewind: dict | None = data.get("rewind")
        self.icm_compare: dict | None = data.get("icm_compare")
        self.blockers_tab: dict | None = data.get("blockers_tab")
        self.lesson: str | None = data.get("lesson")
        self.notes: list[str] = data.get("notes", [])

    @classmethod
    def load(cls, path: str | Path) -> "Spot":
        return cls(json.loads(Path(path).read_text()))

    # -- table helpers --------------------------------------------------
    def seat_names(self) -> list[str]:
        return [row["seat"] for row in self.table]

    def start_stacks(self) -> list[float]:
        return [float(row["stack"]) for row in self.table]

    def seat_index(self, name: str) -> int | None:
        for i, row in enumerate(self.table):
            if row["seat"] == name:
                return i
        return None

    def start_stack(self, name: str) -> float | None:
        i = self.seat_index(name)
        return None if i is None else float(self.table[i]["stack"])

    def behind(self, name: str) -> float | None:
        if name in self.stacks_behind:
            return float(self.stacks_behind[name])
        return None

    def committed(self, name: str) -> float | None:
        s, b = self.start_stack(name), self.behind(name)
        if s is None or b is None:
            return None
        return s - b
