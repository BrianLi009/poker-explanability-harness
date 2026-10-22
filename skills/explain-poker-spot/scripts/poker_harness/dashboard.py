"""Render a spot and its report as one self-contained HTML dashboard.

The page has no external dependencies except two Google Fonts, so it can be
published as a Claude artifact or opened from disk. Panels appear only when
the spot has the data for them:

* the table: stacks, who covers whom, pot
* the range grid: 13x13 classes coloured by action (GTO Wizard's colour
  language), with the borderline hands outlined, for the hero and for the
  responder
* the global shape: each action's frequency and compact range
* borderline ladders: each family from strongest to weakest, coloured by
  action, with the border hands marked
* EV at the borders
* the response funnel: players who act first, then the responder
* the other lines, card removal comparison, rewind (postflop), coverage and
  the takeaway
"""

from __future__ import annotations

import json
import re
from pathlib import Path

from .cards import RANKS, all_hand_classes, cards_str
from .framework import Report
from .shape import FAMILIES, build_shape, norm_class
from .spot import HandRow, Spot

TEMPLATE_PATH = Path(__file__).with_name("dashboard_template.html")


def _class_rows(rows: list[HandRow], complete: bool, fold_action: str | None, actions: list[str]) -> dict:
    """class -> {s: strategy, ev: per-action or None, evb: best EV, w: weight}"""
    out: dict[str, dict] = {}
    for r in rows:
        c = norm_class(r.hand)
        if not c or not r.strategy:
            continue
        if c in out and len(r.hand) == 4:
            continue  # keep the first combo row as the class sample
        out[c] = {
            "s": {a: round(float(v), 1) for a, v in r.strategy.items()},
            "ev": {a: round(float(v), 3) for a, v in r.ev.items()} if r.ev else None,
            "evb": r.ev_best,
            "w": r.weight,
            "label": r.label,
        }
    if complete and fold_action:
        for c in all_hand_classes():
            if c not in out:
                out[c] = {"s": {a: (100.0 if a == fold_action else 0.0) for a in actions}, "ev": None, "evb": 0.0, "w": None, "label": None}
    return out


def _response_path(spot: Spot) -> list[dict]:
    path = spot.data.get("response_path") or []
    out = []
    for p in path:
        acts = {a: float(v) for a, v in (p.get("actions") or {}).items()}
        fold = next((v for a, v in acts.items() if a.lower().startswith("fold")), None)
        out.append({"player": p.get("player"), "actions": acts, "fold": fold, "note": p.get("note")})
    return out


def dashboard_data(spot: Spot, report: Report) -> dict:
    node = spot.node
    actions = list(node.actions) if node else []
    fold_action = next((a for a in actions if a.lower().startswith("fold")), None)
    complete = bool(spot.data.get("hands_complete"))
    shape = build_shape(node.actions, spot.hands, complete) if (node and spot.module == "preflop") else None

    hero_grid = _class_rows(spot.hands, complete, fold_action, actions) if spot.hands else {}
    resp = spot.response
    resp_actions = list(resp.actions) if resp else []
    resp_grid = _class_rows(resp.hands, False, None, resp_actions) if (resp and resp.hands) else {}

    def facts(key: str) -> dict:
        s = report.get(key)
        return s.facts if (s and s.covered) else {}

    lesson = report.get("lesson")
    lessons = []
    if lesson:
        body = lesson.body
        lessons = [lesson.facts.get("lesson")] + [m.strip() for m in re.findall(r"^- (.+)$", body.split("Notes:")[0], re.M)]

    border_hands: dict[str, str] = {}
    if shape:
        for b in shape.borders:
            border_hands[b["worst"]] = "in"
            if b["below"]:
                border_hands.setdefault(b["below"], "out")
            for g in b["gaps"]:
                border_hands.setdefault(g, "out")

    ev_border = []
    if shape:
        seen = set()
        for b in shape.borders:
            for h in (b["worst"], b["below"]):
                if h and h not in seen and h in shape.ev:
                    seen.add(h)
                    ev_border.append({"hand": h, "ev": shape.ev[h], "takes": max(shape.strategy.get(h, {"?": 0}), key=shape.strategy.get(h, {"?": 0}).get)})
        for h, e in shape.ev.items():
            if h not in seen:
                seen.add(h)
                st = shape.strategy.get(h, {})
                ev_border.append({"hand": h, "ev": e, "takes": max(st, key=st.get) if st else None})

    data = {
        "title": spot.title,
        "source": spot.source,
        "module": spot.module,
        "format": spot.format,
        "hero": spot.hero,
        "villain": spot.villain,
        "table": [
            {"seat": r["seat"], "stack": r["stack"], "behind": spot.behind(r["seat"])}
            for r in spot.table
        ],
        "history": spot.history,
        "pot": spot.pot,
        "board": cards_str(spot.board, pretty=False, sep=" ").split() if spot.board else [],
        "scene": facts("scene"),
        "node": {"player": node.player, "actions": node.actions, "combos": node.combos} if node else None,
        "fold_action": fold_action,
        "ranges_by_action": shape.ranges if shape else {},
        "hero_hand": {
            "hand": spot.hero_hand.hand,
            "class": norm_class(spot.hero_hand.hand),
            "strategy": spot.hero_hand.strategy,
            "ev": spot.hero_hand.ev,
            "ev_best": spot.hero_hand.ev_best,
        } if spot.hero_hand else None,
        "grid": hero_grid,
        "grid_complete": complete,
        "border_hands": border_hands,
        "borders": shape.borders if shape else [],
        "families": [{"key": f.key, "name": f.name, "members": f.members} for f in FAMILIES],
        "ev_border": ev_border,
        "response": {
            "player": resp.player,
            "facing": resp.facing,
            "actions": resp.actions,
            "pot_odds": resp.pot_odds,
            "note": resp.note,
            "grid": resp_grid,
        } if resp else None,
        "response_path": _response_path(spot),
        "response_facts": facts("response"),
        "alternatives": facts("alternatives").get("alternatives", []),
        "blockers": facts("blockers"),
        "ranges_facts": facts("ranges"),
        "equity": spot.equity,
        "breakdown": spot.breakdown,
        "rewind": spot.rewind,
        "board_facts": facts("board"),
        "icm": facts("icm"),
        "coverage": report.coverage(),
        "lessons": [x for x in lessons if x],
        "notes": spot.notes,
        "ranks": RANKS,
    }
    return data


def render_dashboard(spot: Spot, report: Report) -> str:
    data = dashboard_data(spot, report)
    payload = json.dumps(data, default=str).replace("</", "<\\/")
    html = TEMPLATE_PATH.read_text()
    title = re.sub(r"[<>&]", "", spot.data.get("dashboard_title") or _short_title(spot))
    return html.replace("__TITLE__", title).replace("__DATA__", payload)


def _short_title(spot: Spot) -> str:
    """Two-to-four word page name, e.g. 'HJ 11bb Jam' or 'SB River Shove'."""
    node = spot.node
    if not node:
        return "Spot Breakdown"
    main = max(node.actions, key=node.actions.get) if node.actions else ""
    if main.lower().startswith("fold") and len(node.actions) > 1:
        rest = {a: v for a, v in node.actions.items() if not a.lower().startswith("fold")}
        main = max(rest, key=rest.get)
    verb = "Jam" if re.search(r"all[\s-]?in|jam|shove", main, re.I) else main.split()[0].capitalize() if main else "Spot"
    street = {3: "Flop", 4: "Turn", 5: "River"}.get(len(spot.board), "Preflop")
    eff = spot.behind(spot.hero)
    depth = f" {eff:g}bb" if eff is not None and street == "Preflop" else ""
    return f"{spot.hero}{depth} {street} {verb}".replace("  ", " ")
