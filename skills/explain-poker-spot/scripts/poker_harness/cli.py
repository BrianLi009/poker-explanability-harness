"""Command line: ``python3 scripts/harness.py <command> ...`` (or ``python -m poker_harness`` once installed).

Commands
--------
explain SPOT.json [--format md|json|brief] [-o OUT]
    Build the explanation for a captured spot.
dashboard SPOT.json [-o OUT.html]
    Render the spot as a self-contained HTML dashboard.
inline SPOT.json [-o OUT.html]
    Render a compact HTML fragment to show inside the chat.
check SPOT.json EXPLANATION.md
    Score a written explanation against the framework.
validate SPOT.json
    List data problems in a spot file.
board CARDS
    Quick board read: texture and, on the river, which cards beat the board.
icm --stacks 30 20 10 --payouts 50 30 20 --hero 2 --villain 0
    Bubble factor and call requirements between two players.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from . import explain, load_spot, validate
from .board import board_beaters, texture
from .brief import build_brief, check_explanation
from .cards import parse_cards
from .icm import allin_call_requirements, bubble_factor, describe_bubble_factor, icm_equities


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="poker_harness", description="Explain GTO Wizard spots.")
    sub = p.add_subparsers(dest="cmd", required=True)

    e = sub.add_parser("explain", help="explain a captured spot")
    e.add_argument("spot")
    e.add_argument("--format", choices=["md", "json", "brief"], default="md")
    e.add_argument("-o", "--out")

    d = sub.add_parser("dashboard", help="render an HTML dashboard for a spot")
    d.add_argument("spot")
    d.add_argument("-o", "--out", default=None, help="output .html (default: next to the spot)")

    n = sub.add_parser("inline", help="render a compact visual to show inside the chat")
    n.add_argument("spot")
    n.add_argument("-o", "--out", default=None, help="output .html fragment (default: stdout)")

    c = sub.add_parser("check", help="score a written explanation")
    c.add_argument("spot")
    c.add_argument("explanation")

    v = sub.add_parser("validate", help="check a spot file")
    v.add_argument("spot")

    b = sub.add_parser("board", help="read a board")
    b.add_argument("cards")

    i = sub.add_parser("icm", help="ICM pressure between two players")
    i.add_argument("--stacks", type=float, nargs="+", required=True)
    i.add_argument("--payouts", type=float, nargs="+", required=True)
    i.add_argument("--hero", type=int, required=True, help="index into --stacks")
    i.add_argument("--villain", type=int, required=True)
    i.add_argument("--hero-committed", type=float, default=0.0)
    i.add_argument("--dead", type=float, default=0.0)

    a = p.parse_args(argv)

    if a.cmd == "explain":
        report = explain(a.spot)
        if a.format == "md":
            text = report.to_markdown()
        elif a.format == "json":
            text = report.to_json()
        else:
            text = build_brief(report)
        if a.out:
            Path(a.out).write_text(text)
        else:
            sys.stdout.write(text)
        return 0

    if a.cmd == "dashboard":
        from .dashboard import render_dashboard

        spot = load_spot(a.spot)
        html = render_dashboard(spot, explain(spot))
        out = Path(a.out) if a.out else Path(a.spot).with_suffix(".dashboard.html")
        out.write_text(html)
        print(out)
        return 0

    if a.cmd == "inline":
        from .inline import render_inline

        spot = load_spot(a.spot)
        frag = render_inline(spot, explain(spot))
        if a.out:
            Path(a.out).write_text(frag)
            print(a.out)
        else:
            sys.stdout.write(frag)
        return 0

    if a.cmd == "check":
        report = explain(a.spot)
        res = check_explanation(Path(a.explanation).read_text(), report, source=load_spot(a.spot).data)
        print(json.dumps(res, indent=2))
        return 0

    if a.cmd == "validate":
        issues = validate(load_spot(a.spot))
        if not issues:
            print("OK")
            return 0
        print("\n".join(f"- {x}" for x in issues))
        return 1

    if a.cmd == "board":
        cards = parse_cards(a.cards)
        t = texture(cards)
        print(t.summary())
        for n in t.notes:
            print(f"- {n}")
        if len(cards) == 5:
            bb = board_beaters(cards)
            print(bb.describe())
            if bb.two_card_only:
                print("Two-card improvements: " + ", ".join(bb.two_card_only[:30]))
        return 0

    if a.cmd == "icm":
        eqs = icm_equities(a.stacks, a.payouts)
        print("ICM equity: " + ", ".join(f"[{k}] {s:g} -> {e:.2f}" for k, (s, e) in enumerate(zip(a.stacks, eqs))))
        bf = bubble_factor(a.stacks, a.payouts, a.hero, a.villain)
        print(f"Bubble factor hero[{a.hero}] vs villain[{a.villain}]: {bf:.2f} ({describe_bubble_factor(bf)})")
        m = allin_call_requirements(a.stacks, a.payouts, a.hero, a.villain, hero_committed=a.hero_committed, dead_money=a.dead)
        print(
            f"Calling villain's all-in: chip EV needs {100 * m.chip_required:.1f}% equity, "
            f"ICM needs {100 * m.icm_required:.1f}% (risk premium {100 * m.risk_premium:.1f}%)."
        )
        return 0
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
