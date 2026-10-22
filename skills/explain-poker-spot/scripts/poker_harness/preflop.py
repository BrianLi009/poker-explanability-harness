"""Preflop module: explain a preflop node captured from GTO Wizard.

Adds three things a preflop breakdown needs on top of the shared sections:

* stack-depth context (push/fold, re-shove and open-raise regimes),
* hand-family patterns in the grid (e.g. A5s jamming more than A9s),
* preflop card removal (what your hand does to the opponent's range).
"""

from __future__ import annotations

from .cards import RANKS, class_combos, hand_class, parse_cards
from .framework import TITLES, Report, Section
from .sections import (
    Context,
    actions_line,
    alternatives_section,
    blockers_section,
    decision_section,
    hero_hand_section,
    icm_section,
    lesson_section,
    outliers_section,
    pct,
    pretty_hand,
    range_first_section,
    ranges_section,
    response_section,
    rewind_section,
    scene_section,
    table,
)
from .spot import HandRow, Spot


def stack_regime(bb: float) -> str:
    if bb <= 12:
        return "push/fold depth: most hands either shove or fold, and flatting is rare"
    if bb <= 20:
        return "re-shove depth: 3-bet shoves replace most 3-bets, and opens get smaller"
    if bb <= 35:
        return "middle depth: min-raise opens, some limps from the SB, and 3-bet/jam vs 3-bet/fold decisions"
    if bb <= 60:
        return "standard MTT depth: normal opens and 3-bets, with 4-bet shoves as the main pressure"
    return "deep: postflop play matters more, so hands with playability gain value"


FAMILIES = [
    ("Pocket pairs", lambda c: len(c) == 2),
    ("Suited aces", lambda c: c[0] == "A" and c.endswith("s")),
    ("Offsuit aces", lambda c: c[0] == "A" and c.endswith("o")),
    ("Suited kings", lambda c: c[0] == "K" and c.endswith("s")),
    ("Offsuit kings", lambda c: c[0] == "K" and c.endswith("o")),
    ("Suited connectors", lambda c: len(c) == 3 and c.endswith("s") and RANKS.index(c[0]) - RANKS.index(c[1]) == 1 and c[0] not in "AK"),
]


def _class_of_row(row: HandRow) -> str | None:
    h = row.hand
    if len(h) == 4 and h[1] in "cdhs":
        return hand_class(parse_cards(h))
    if len(h) in (2, 3):
        return h[0].upper() + h[1].upper() + h[2:].lower()
    return None


def _aggressive_actions(actions: dict[str, float]) -> list[str]:
    words = ("allin", "all-in", "all in", "jam", "shove", "raise", "bet", "3bet", "4bet")
    return [a for a in actions if any(w in a.lower() for w in words)]


def _is_allin_name(a: str) -> bool:
    return any(w in a.lower() for w in ("allin", "all-in", "all in", "jam", "shove"))


def family_patterns_section(ctx: Context) -> Section | None:
    """Hand-family patterns: aggression that isn't monotone in strength, and sizing splits."""
    s = ctx.spot
    if not s.node or not s.hands:
        return None
    aggr = _aggressive_actions(s.node.actions)
    if not aggr:
        return None
    jam = next((a for a in aggr if _is_allin_name(a)), None)
    small = [a for a in aggr if a != jam]
    rows = {}
    for r in s.hands:
        c = _class_of_row(r)
        if c and r.strategy:
            rows[c] = r.strategy
    agg_of = {c: sum(st.get(a, 0.0) for a in aggr) for c, st in rows.items()}
    findings = []
    sizing = []
    for fam, pred in FAMILIES:
        members = [c for c in rows if pred(c)]
        if len(members) < 3:
            continue
        members.sort(key=lambda c: (RANKS.index(c[1]) if len(c) > 2 else RANKS.index(c[0])), reverse=True)
        for i, weaker in enumerate(members):
            stronger = [m for m in members[:i] if agg_of[m] + 30 <= agg_of[weaker]]
            if stronger:
                findings.append((fam, weaker, agg_of[weaker], stronger[-1], agg_of[stronger[-1]]))
        if jam and small:
            for c in members:
                j = rows[c].get(jam, 0.0)
                sm = sum(rows[c].get(a, 0.0) for a in small)
                if j + sm >= 50:
                    sizing.append((fam, c, j, sm))
    if not findings and not sizing:
        return None
    parts = []
    label = " + ".join(aggr)
    if findings:
        rows_t = [[fam, w, pct(fw), s_, pct(fs)] for fam, w, fw, s_, fs in findings[:10]]
        parts.append(
            f"Hands that are more aggressive ({label}) than stronger hands of the same family:\n\n"
            + table(["Family", "Weaker hand", "Aggressive %", "Stronger hand", "Aggressive %"], rows_t)
            + "\n\nWhen a weaker hand is more aggressive, the usual reasons are blockers (an ace or king removes the opponent's best continues), "
            "playability (the stronger hand prefers to call and see a flop), or the weaker hand being the better bluff because it has less showdown value. "
            "The solver doesn't label which; the blockers section shows what each hand removes from the opponent's range."
        )
        f0 = findings[0]
        ctx.lesson(4, f"{f0[1]} is more aggressive than {f0[3]} ({pct(f0[2])} vs {pct(f0[4])}): aggression goes to the hands with the right blockers and the least to lose by folding later, not simply the strongest.")
    if sizing:
        rows_t = [[fam, c, pct(j), pct(sm), jam if j > sm else " / ".join(small)] for fam, c, j, sm in sizing]
        parts.append(
            f"How the aggressive hands split between the all-in ({jam}) and the smaller raise ({', '.join(small)}):\n\n"
            + table(["Family", "Hand", jam, " + ".join(small), "Prefers"], rows_t[:16])
        )
        top_small = [c for fam, c, j, sm in sizing if sm > j]
        top_jam = [c for fam, c, j, sm in sizing if j >= sm]
        if top_small and top_jam:
            parts.append(
                f"The small raise goes to {', '.join(top_small[:6])}; the all-in goes to {', '.join(top_jam[:6])}. "
                "Typically the strongest hands raise small because they want to be called or face a re-raise, "
                "while hands that play badly after the flop or need fold equity prefer to get it in now."
            )
            ctx.lesson(5, f"Sizing is split by hand type: {', '.join(top_small[:3])} raise small, {', '.join(top_jam[:3])} jam.")
    return Section("outliers", "Hand-family patterns", "\n\n".join(parts), {"findings": findings, "sizing": sizing}, inference=True)


def _neighbours(cls: str) -> list[str]:
    """Same-family hands one step stronger and weaker (A4s -> A5s, A3s; 77 -> 88, 66)."""
    out = []
    if len(cls) == 2:
        r = RANKS.index(cls[0])
        for d in (1, -1):
            if 0 <= r + d < 13:
                out.append(RANKS[r + d] * 2)
        return out
    hi, lo, kind = cls[0], RANKS.index(cls[1]), cls[2:]
    for d in (1, -1):
        k = lo + d
        if 0 <= k < RANKS.index(hi):
            out.append(hi + RANKS[k] + kind)
    return out


def _hand_cards(h: str) -> list[int]:
    return parse_cards(h) if len(h) == 4 and h[1] in "cdhs" else list(class_combos(h)[0])


def preflop_blockers_section(ctx: Context) -> Section | None:
    s = ctx.spot
    vr = s.ranges.get(s.villain)
    if not s.hero_hand or vr is None:
        return None
    h = s.hero_hand.hand
    hero = _hand_cards(h)
    before = vr.by_class()
    after = vr.without(hero).by_class()
    tot_b, tot_a = sum(before.values()), sum(after.values())
    lines = []
    facts: dict = {"removed": tot_b - tot_a, "total": tot_b}
    resp = s.response
    cont_key = next((a for a in resp.actions if not a.lower().startswith("fold")), None) if resp else None
    if resp and resp.hands and cont_key:
        cont_of = {}
        for r in resp.hands:
            c = _class_of_row(r)
            if c:
                cont_of[c] = r.strategy.get(cont_key, 0.0) / 100.0

        def split(by_cls: dict[str, float]) -> tuple[float, float]:
            cont = sum(w * cont_of.get(c, 0.0) for c, w in by_cls.items())
            return cont, sum(by_cls.values()) - cont

        def removal(cards: list[int]) -> tuple[float, float, float]:
            ca, fa = split(vr.without(cards).by_class())
            return 100 * (cb - ca) / cb, 100 * (fb - fa) / fb, 100 * fa / (ca + fa)

        cb, fb = split(before)
        if cb > 0 and fb > 0:
            p_before = 100 * fb / (cb + fb)
            rc, rf, p_after = removal(hero)
            facts.update(cont_removed_pct=rc, fold_removed_pct=rf, fold_before=p_before, fold_after=p_after)
            verb = cont_key.split()[0].lower()
            lines.append(
                f"Holding {pretty_hand(h)} removes {pct(rc)} of {s.villain}'s {verb}ing combos but {pct(rf)} of its folding combos. "
                f"That moves {s.villain}'s fold frequency from {pct(p_before)} (no card removal) to {pct(p_after)} against this hand."
            )
            node_fold = next((v for a, v in resp.actions.items() if a.lower().startswith("fold")), None)
            if node_fold is not None:
                if abs(node_fold - p_before) <= 1.0:
                    lines.append(
                        f"_Check: rebuilt from the captured rows, {s.villain} folds {pct(p_before)}, matching GTO Wizard's {pct(node_fold)}, so the rows are complete._"
                    )
                else:
                    ctx.spot.data.setdefault("_warnings", []).append(
                        f"Response rows rebuild a {pct(p_before)} fold frequency but the node shows {pct(node_fold)}: some {verb}ing classes are probably missing from `response.hands` (unlisted classes count as folds)."
                    )
            if rc > rf + 3:
                ctx.lesson(6, f"{pretty_hand(h)} blocks {s.villain}'s continuing hands ({pct(rc)} removed) more than its folds ({pct(rf)}), which helps make it a candidate for aggression.")
            elif rf > rc + 3:
                lines.append(f"{pretty_hand(h)} blocks more of {s.villain}'s folds than its continues, so it gets fewer folds than an average hand would.")

            # Compare with nearby hands, e.g. why A4s jams more than A5s.
            compare = list(s.data.get("compare_hands") or [])
            hero_cls = _class_of_row(s.hero_hand)
            if not compare and hero_cls:
                rows_by_cls = {_class_of_row(r): r for r in s.hands}
                compare = [c for c in _neighbours(hero_cls) if c in rows_by_cls]
            if compare:
                aggr = [a for a in (s.node.actions if s.node else {}) if any(w in a.lower() for w in ("allin", "all-in", "jam", "shove", "raise"))]
                rows_by_cls = {_class_of_row(r): r for r in s.hands}
                table_rows = []
                comp_facts = {}
                for name in [h] + compare:
                    cards = _hand_cards(name)
                    c_rc, c_rf, c_fold = removal(cards)
                    row = rows_by_cls.get(_class_of_row(HandRow(hand=name)))
                    strat = actions_line({a: row.strategy.get(a, 0.0) for a in aggr}) if row and aggr else "–"
                    table_rows.append([pretty_hand(name), pct(c_rc), pct(c_rf), pct(c_fold), strat])
                    comp_facts[name] = {"cont_removed_pct": c_rc, "fold_removed_pct": c_rf, "villain_fold_pct": c_fold}
                facts["compare"] = comp_facts
                lines.append(
                    "Compared with nearby hands:\n\n"
                    + table(["Hand", f"{s.villain} {verb}s removed", "Folds removed", f"{s.villain} folds", "Aggressive actions"], table_rows)
                )
                folds = [v["villain_fold_pct"] for v in comp_facts.values()]
                if max(folds) - min(folds) < 1.0:
                    lines.append(
                        "The fold frequencies are nearly identical, so card removal alone doesn't explain why these hands differ. "
                        "The rest of the difference likely comes from how each hand does when called or when it calls instead (equity, playability); capture those nodes to show it."
                    )
    rows = []
    for cls in sorted(before, key=lambda c: -before[c]):
        b, a = before[cls], after.get(cls, 0.0)
        if b - a > 1e-9:
            rows.append([cls, f"{b:.2f}", f"{a:.2f}", pct(100 * (b - a) / b)])
    if not rows:
        lines.append(f"{pretty_hand(h)} shares no cards with {s.villain}'s range, so it blocks nothing.")
    else:
        lines.append(
            f"Overall {pretty_hand(h)} removes {tot_b - tot_a:.1f} of {tot_b:.1f} combos ({pct(100 * (tot_b - tot_a) / tot_b)}) from {s.villain}'s range. Largest classes affected:\n\n"
            + table(["Class", "Combos before", "After", "Removed"], rows[:10])
        )
    return Section("blockers", TITLES["blockers"], "\n\n".join(l for l in lines if l), facts)


def explain_preflop(spot: Spot) -> Report:
    ctx = Context(spot)
    rep = Report(spot.title, "preflop", source=spot.source)
    rep.add(decision_section(ctx))
    scene = scene_section(ctx)
    eff = scene.facts.get("effective")
    if eff is None and spot.table:
        hs, vs = spot.start_stack(spot.hero), spot.start_stack(spot.villain)
        if hs and vs:
            eff = min(hs, vs)
    if eff:
        scene.body += f"\n\n**Stack depth:** {eff:g}bb effective. Typical of this depth in general (not read from this solution): {stack_regime(eff)}."
        scene.covered = True
    rep.add(scene)
    rep.add(ranges_section(ctx, preflop=True))
    rep.add(range_first_section(ctx))
    rep.add(hero_hand_section(ctx))
    fam = family_patterns_section(ctx)
    out = outliers_section(ctx)
    if fam and out.covered:
        out.body += "\n\n### " + fam.title + "\n\n" + fam.body
        out.inference = True
        rep.add(out)
    elif fam:
        rep.add(fam)
    else:
        rep.add(out)
    rep.add(response_section(ctx))
    rep.add(alternatives_section(ctx))
    rep.add(rewind_section(ctx))
    rep.add(preflop_blockers_section(ctx) or blockers_section(ctx))
    rep.add(icm_section(ctx))
    rep.add(lesson_section(ctx))
    rep.warnings += spot.data.get("_warnings", [])
    return rep
