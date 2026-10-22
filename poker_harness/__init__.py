"""Poker explainability harness.

Turns what GTO Wizard shows you (strategies, EVs, ranges, breakdowns,
earlier-street frequencies) into a structured explanation that follows how
good coaches break hands down. It does not solve the game.

    from poker_harness import explain, load_spot
    report = explain(load_spot("examples/river_five_flush_shove.json"))
    print(report.to_markdown())
"""

from __future__ import annotations

from pathlib import Path

from .framework import CHECKLIST, Report, Section
from .postflop import explain_postflop
from .preflop import explain_preflop
from .spot import Spot

__all__ = ["explain", "load_spot", "Spot", "Report", "Section", "CHECKLIST", "validate"]
__version__ = "0.1.0"


def load_spot(path: str | Path) -> Spot:
    return Spot.load(path)


def validate(spot: Spot) -> list[str]:
    """Problems that would make the explanation wrong or thin."""
    issues = []
    names = spot.seat_names()
    for who in (spot.hero, spot.villain):
        if names and who not in names:
            issues.append(f"'{who}' is not a seat in `table` ({', '.join(names)}).")
    if spot.module == "postflop" and not spot.board:
        issues.append("Postflop spots need `board`.")
    if spot.node and spot.node.actions:
        total = sum(spot.node.actions.values())
        if abs(total - 100) > 1.5:
            issues.append(f"`node.actions` add up to {total:.1f}%, not 100%.")
    if spot.response and spot.response.actions:
        total = sum(spot.response.actions.values())
        if abs(total - 100) > 1.5:
            issues.append(f"`response.actions` add up to {total:.1f}%, not 100%.")
    for name in spot.ranges:
        if names and name not in names:
            issues.append(f"Range given for '{name}', which is not a seat in `table`.")
    return issues


def explain(spot: Spot | dict | str | Path) -> Report:
    if isinstance(spot, (str, Path)):
        spot = Spot.load(spot)
    elif isinstance(spot, dict):
        spot = Spot(spot)
    issues = validate(spot)
    report = explain_preflop(spot) if spot.module == "preflop" else explain_postflop(spot)
    report.warnings = issues + report.warnings
    return report
