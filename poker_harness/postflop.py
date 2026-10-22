"""Postflop module: explain a flop, turn or river node captured from GTO Wizard."""

from __future__ import annotations

from .framework import Report
from .sections import (
    Context,
    alternatives_section,
    blockers_section,
    board_section,
    decision_section,
    hero_hand_section,
    icm_section,
    lesson_section,
    outliers_section,
    range_first_section,
    ranges_section,
    response_section,
    rewind_section,
    scene_section,
)
from .spot import Spot


def explain_postflop(spot: Spot) -> Report:
    if not spot.board:
        raise ValueError("A postflop spot needs a board")
    ctx = Context(spot)
    rep = Report(spot.title, "postflop", source=spot.source)
    for build in (
        decision_section,
        scene_section,
        board_section,
        ranges_section,
        range_first_section,
        hero_hand_section,
        outliers_section,
        response_section,
        alternatives_section,
        rewind_section,
        blockers_section,
        icm_section,
    ):
        rep.add(build(ctx))
    rep.add(lesson_section(ctx))
    rep.warnings += spot.data.get("_warnings", [])
    return rep
