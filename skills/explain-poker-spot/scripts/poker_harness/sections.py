"""Section builders shared by the preflop and postflop modules.

Each builder reads the captured GTO Wizard numbers from a ``Spot`` and
returns a ``Section`` of plain-English explanation plus the facts it used.
Builders never invent solver output: when data is missing they return an
uncovered section and the report tells you what to capture.
"""

from __future__ import annotations

import math
import re
from dataclasses import dataclass, field

from . import icm as icm_mod
from .board import blocker_report, board_beaters, classify_combo, composition, showdown_split, texture
from .cards import card_str, cards_str, class_combos, parse_cards
from .framework import TITLES, Section
from .spot import HandRow, Node, Spot, normalise_freq_list

ALLIN_RE = re.compile(r"all[\s-]?in|shove|jam", re.I)


# ---------------------------------------------------------------------------
# Formatting helpers
# ---------------------------------------------------------------------------

def f1(x: float | None, unit: str = "") -> str:
    if x is None:
        return "?"
    if isinstance(x, float) and math.isinf(x):
        return "inf"
    return f"{x:.1f}{unit}"


def f2(x: float | None) -> str:
    return "?" if x is None else f"{x:.2f}"


def pct(x: float | None) -> str:
    return "?" if x is None else f"{x:.1f}%"


def table(headers: list[str], rows: list[list]) -> str:
    out = ["| " + " | ".join(headers) + " |", "|" + "|".join("---" for _ in headers) + "|"]
    for r in rows:
        out.append("| " + " | ".join(str(c) for c in r) + " |")
    return "\n".join(out)


def actions_line(actions: dict[str, float]) -> str:
    items = sorted(actions.items(), key=lambda kv: -kv[1])
    return ", ".join(f"{a} {pct(v)}" for a, v in items)


def is_allin(action: str | None) -> bool:
    return bool(action and ALLIN_RE.search(action))


def pretty_hand(hand: str) -> str:
    """Pretty-print a combo ('AsTs' -> 'A♠T♠'); classes pass through."""
    if len(hand) == 4 and hand[1] in "cdhs" and hand[3] in "cdhs":
        return cards_str(parse_cards(hand), pretty=True)
    return hand


@dataclass
class Context:
    """Shared state while building one report."""

    spot: Spot
    lessons: list[tuple[int, str]] = field(default_factory=list)  # (priority, sentence)
    facts: dict = field(default_factory=dict)

    def lesson(self, priority: int, text: str) -> None:
        self.lessons.append((priority, text))


def _uncovered(key: str) -> Section:
    return Section(key, TITLES[key], covered=False)


# ---------------------------------------------------------------------------
# 1. Decision vs result
# ---------------------------------------------------------------------------

def decision_section(ctx: Context) -> Section:
    later = "the board that came" if not ctx.spot.board else "the cards that came later"
    body = (
        "This explanation judges the decision with only the information available when it was made. "
        f"Who won the pot, or {later}, doesn't change whether the play was right; "
        "if a different runout would flip the verdict, we'd be grading the result instead of the decision."
    )
    return Section("decision", TITLES["decision"], body)


# ---------------------------------------------------------------------------
# 2. Scene
# ---------------------------------------------------------------------------

def scene_section(ctx: Context) -> Section:
    s = ctx.spot
    lines: list[str] = []
    facts: dict = {}
    fmt = s.format
    if fmt:
        bits = [str(fmt[k]) for k in ("game", "structure", "phase") if fmt.get(k)]
        if fmt.get("players_total"):
            bits.append(f"{fmt['players_total']} entrants")
        if fmt.get("players_left"):
            bits.append(f"{fmt['players_left']} left")
        if fmt.get("icm"):
            bits.append("ICM applies")
        if fmt.get("average_stack"):
            bits.append(f"average stack {fmt['average_stack']}bb")
        lines.append("**Format:** " + ", ".join(bits) + ".")
    if s.table:
        cells = []
        for row in s.table:
            name = row["seat"]
            tag = " (hero)" if name == s.hero else " (villain)" if name == s.villain else ""
            cells.append(f"{name} {row['stack']:g}bb{tag}")
        lines.append("**Stacks at the start of the hand:** " + ", ".join(cells) + ".")
    if s.history:
        hist = "; ".join(
            f"{h.get('street', '').capitalize()}"
            + (f" [{cards_str(parse_cards(h['board']), True, ' ')}]" if h.get("board") else "")
            + f": {h.get('actions', '')}"
            for h in s.history
        )
        lines.append(f"**Action so far:** {hist}.")
    hb, vb = s.behind(s.hero), s.behind(s.villain)
    if s.pot is not None:
        lines.append(f"**Pot:** {s.pot:g}bb.")
        facts["pot"] = s.pot
    if hb is not None and vb is not None:
        eff = min(hb, vb)
        facts.update(hero_behind=hb, villain_behind=vb, effective=eff)
        covers = s.hero if hb > vb else s.villain if vb > hb else None
        line = f"**Behind:** {s.hero} {hb:g}bb, {s.villain} {vb:g}bb, so {eff:g}bb effective"
        if s.pot:
            spr = eff / s.pot
            facts["spr"] = spr
            line += f" and a stack-to-pot ratio of {spr:.1f}"
        line += "."
        lines.append(line)
        if covers:
            covered = s.villain if covers == s.hero else s.hero
            facts["covers"] = covers
            lines.append(
                f"{covers} covers {covered}: if they get it all in, {covered} is the one who can bust. "
                + ("In a tournament that asymmetry matters for ICM (see below)." if fmt.get("icm") else "")
            )
    if not lines:
        return _uncovered("scene")
    return Section("scene", TITLES["scene"], "\n\n".join(lines), facts)


# ---------------------------------------------------------------------------
# 3. Board (postflop)
# ---------------------------------------------------------------------------

def board_section(ctx: Context) -> Section:
    s = ctx.spot
    if not s.board:
        return _uncovered("board")
    t = texture(s.board)
    lines = [f"**Board:** {t.summary()}."]
    lines += t.notes
    facts: dict = {"texture": t.suit_pattern, "street": t.street}
    if t.street == "river":
        bb = board_beaters(s.board)
        facts["single_card_outs"] = [card_str(c) for c in bb.single_card_outs]
        if bb.single_card_outs:
            n = len(bb.single_card_outs)
            lines.append(
                f"{'Only ' if n <= 8 else ''}{n} specific card{'s' if n > 1 else ''} beat{'s' if n == 1 else ''} the board on {'their' if n > 1 else 'its'} own: "
                + bb.outs_text()
                + ". Everything else needs both hole cards to improve, or plays the board."
            )
            unseen = 52 - 5
            p_one = 1 - math.comb(unseen - n, 2) / math.comb(unseen, 2)
            facts["random_hand_has_out"] = p_one
        if bb.single_card_outs and len(bb.single_card_outs) <= 8:
            lines.append(
                f"Combinatorics check: a random two-card hand holds at least one of those {n} cards "
                f"{pct(100 * p_one)} of the time (1 − C({unseen - n},2)/C({unseen},2)), before range effects."
            )
        if bb.two_card_only and len(bb.two_card_only) <= 12:
            lines.append("Hands that improve only with both cards: " + ", ".join(bb.two_card_only) + ".")
        # Plays-the-board share per player, if ranges are known.
        shares = {}
        for name, rng in s.ranges.items():
            if name in s.partial_ranges:
                continue
            comp = composition(rng, s.board)
            pb = comp.get("Plays the board")
            if pb:
                shares[name] = pb["pct"]
        if shares:
            facts["plays_board_pct"] = shares
            lines.append(
                "Share of each range that just plays the board (a chop against each other): "
                + ", ".join(f"{k} {pct(v)}" for k, v in shares.items())
                + "."
            )
            if min(shares.values()) >= 50:
                ctx.lesson(
                    6,
                    "When most of both ranges play the board, the river is a fight over who keeps their share of the pot, not who has the best hand.",
                )
    return Section("board", TITLES["board"], "\n\n".join(lines), facts)


# ---------------------------------------------------------------------------
# 4. Ranges
# ---------------------------------------------------------------------------

def ranges_section(ctx: Context, preflop: bool = False) -> Section:
    s = ctx.spot
    parts: list[str] = []
    facts: dict = {}
    if s.equity:
        rows = []
        for name, e in s.equity.items():
            rows.append([name, f1(e.get("combos")), pct(e.get("equity")), pct(e.get("eqr")), f2(e.get("ev")) if e.get("ev") is not None else "–"])
        parts.append(table(["Player", "Combos", "Equity", "EQR", "EV (bb)"], rows))
        facts["equity"] = s.equity
        names = list(s.equity)
        if len(names) == 2:
            a, b = names
            ea, eb = s.equity[a].get("equity"), s.equity[b].get("equity")
            if ea is not None and eb is not None:
                lead = a if ea > eb else b
                diff = abs(ea - eb)
                word = "a near coin-flip" if diff < 5 else "a clear edge" if diff < 15 else "a big edge"
                parts.append(f"{lead} has the equity lead, {pct(max(ea, eb))} to {pct(min(ea, eb))}: {word}.")
            ca, cb = s.equity[a].get("combos"), s.equity[b].get("combos")
            if ca and cb:
                ratio = max(ca, cb) / min(ca, cb)
                if ratio >= 1.5:
                    wide = a if ca > cb else b
                    parts.append(f"{wide}'s range is {ratio:.1f}x wider in combos, so it is weighted toward more medium and weak hands.")
            for n in names:
                eqr = s.equity[n].get("eqr")
                if eqr is not None and (eqr < 90 or eqr > 110):
                    parts.append(
                        f"{n}'s EQR is {pct(eqr)}: it {'realises less' if eqr < 100 else 'realises more'} than its raw equity, "
                        f"usually because of {'position or stack pressure working against it' if eqr < 100 else 'position or the initiative'}."
                    )
    if s.breakdown:
        for name, cats in s.breakdown.items():
            rows = [[c.get("category"), pct(c.get("pct")), f1(c.get("combos")), actions_line(c["strategy"]) if c.get("strategy") else ""] for c in cats]
            parts.append(f"**{name} by hand category** (Breakdown tab):\n\n" + table(["Category", "Range %", "Combos", "Strategy"], rows))
        facts["breakdown"] = s.breakdown
        big = {n: max(c, key=lambda c: c.get("pct", 0)) for n, c in s.breakdown.items() if c}
        if big:
            parts.append(
                "Biggest category in each range: "
                + "; ".join(f"{n}: {c.get('category')} ({pct(c.get('pct'))})" for n, c in big.items())
                + "."
            )
    elif s.ranges and s.board:
        for name, rng in s.ranges.items():
            if name in s.partial_ranges:
                continue
            comp = composition(rng, s.board)
            rows = [[k, f1(g["combos"]), pct(g["pct"]), " ".join(pretty_hand(e) for e in g["examples"][:4])] for k, g in comp.items()]
            parts.append(f"**{name} composition** (computed from the range you supplied):\n\n" + table(["Group", "Combos", "Share", "Examples"], rows))
    if preflop and s.node and s.node.actions:
        fold = next((v for a, v in s.node.actions.items() if a.lower().startswith("fold")), None)
        if fold is not None:
            cont = 100 - fold
            parts.append(
                f"{s.node.player} continues with {pct(cont)} of hands (about {13.26 * cont:.0f} combos) and folds the rest."
            )
            facts["continue_pct"] = cont
    if preflop and s.ranges:
        widths = {n: r.percent_of_hands() for n, r in s.ranges.items()}
        facts["range_width_pct"] = widths
        parts.append("Range widths: " + ", ".join(f"{n} {pct(w)} of hands ({r.total():.0f} combos)" for (n, w), r in zip(widths.items(), s.ranges.values())) + ".")
    if not parts:
        return _uncovered("ranges")
    sec = Section("ranges", TITLES["ranges"], "\n\n".join(parts), facts)
    if not s.equity and not s.breakdown:
        sec.partial = "No equity chart or breakdown captured, so range strength and categories aren't shown. Capture the Equity chart (equity, EQR, combos) and Breakdown tab for both players."
    return sec


# ---------------------------------------------------------------------------
# 5. Whole-range strategy
# ---------------------------------------------------------------------------

def range_first_section(ctx: Context) -> Section:
    node = ctx.spot.node
    if not node or not node.actions:
        return _uncovered("range_first")
    used = {a: v for a, v in node.actions.items() if v >= 1.0}
    unused = [a for a, v in node.actions.items() if v < 1.0]
    lines = [f"Facing this spot, {node.player}'s whole range plays: {actions_line(used)}."]
    if node.combos:
        lines.append("In combos: " + ", ".join(f"{a} {v:.1f}" for a, v in node.combos.items() if v >= 0.05) + ".")
    if unused:
        lines.append(f"Essentially never used: {', '.join(unused)}. When an option is skipped, ask what it would do worse than the chosen ones.")
    if len(used) >= 2:
        top = sorted(used.values(), reverse=True)
        if top[0] - top[1] < 25:
            lines.append("The range splits fairly evenly between options, so the interesting question is *which* hands go where (see outliers).")
    sizes = [a for a in used if is_allin(a)]
    if sizes and used[sizes[0]] >= 30:
        lines.append(
            f"{node.player} goes all-in with {pct(used[sizes[0]])} of the range. With a bet that large, check what the shoving hands are: "
            "only very strong hands and bluffs (polarised), or also medium hands that can't stand a bet if they check."
        )
    return Section("range_first", TITLES["range_first"], "\n\n".join(lines), {"actions": node.actions, "combos": node.combos})


# ---------------------------------------------------------------------------
# 6. Hero hand and EV
# ---------------------------------------------------------------------------

def hero_hand_section(ctx: Context) -> Section:
    s = ctx.spot
    h = s.hero_hand
    if not h:
        return _uncovered("hero_hand")
    lines: list[str] = []
    facts: dict = {"hand": h.hand}
    lines.append(f"**Hand:** {pretty_hand(h.hand)}" + (f" ({h.label})" if h.label else ""))
    if s.board and len(h.hand) == 4:
        info = classify_combo(parse_cards(h.hand), s.board)
        facts["made"] = info["label"]
        lines[-1] += f", which makes: {info['label']}" + (f" + {', '.join(info['draws'])}" if info["draws"] else "") + "."
    else:
        lines[-1] += "."
    if h.strategy:
        lines.append(f"Solver strategy for this hand: {actions_line(h.strategy)}.")
    if h.ev:
        evs = sorted(h.ev.items(), key=lambda kv: -kv[1])
        lines.append("EV by action: " + ", ".join(f"{a} {v:.2f}bb" for a, v in evs) + ".")
        if len(evs) >= 2:
            gap = evs[0][1] - evs[1][1]
            facts["ev_gap"] = gap
            pot = s.pot or 0
            rel = 100 * gap / pot if pot else None
            if gap < 0.15 or (rel is not None and rel < 1.5):
                lines.append(
                    f"The top two actions are within {gap:.2f}bb"
                    + (f" ({rel:.1f}% of the pot)" if rel is not None else "")
                    + ", so the hand is close to indifferent. That is why the solver mixes: choosing either is fine, "
                    "and the mix matters only to keep the range balanced."
                )
                ctx.lesson(3, f"With {pretty_hand(h.hand)} the options are worth almost the same ({gap:.2f}bb apart), so the frequency matters more for the range than for the hand.")
            else:
                lines.append(
                    f"{evs[0][0]} is better by {gap:.2f}bb"
                    + (f" ({rel:.1f}% of the pot)" if rel is not None else "")
                    + ". A gap like that is a real mistake if you pick the wrong action, even if it looks small per hand."
                )
    if h.equity is not None:
        lines.append(f"Equity against the opponent's range: {pct(h.equity)}.")
    if s.node and h.strategy and s.node.actions:
        mine = max(h.strategy, key=h.strategy.get)
        rng = s.node.actions.get(mine, 0.0)
        diff = h.strategy[mine] - rng
        if abs(diff) >= 25:
            lines.append(
                f"This hand plays {mine} {pct(h.strategy[mine])} of the time against {pct(rng)} for the range as a whole, "
                "so it is an outlier: the explanation has to say what this hand gains from that action that most of the range doesn't."
            )
    return Section("hero_hand", TITLES["hero_hand"], "\n\n".join(lines), facts)


# ---------------------------------------------------------------------------
# 7. Outliers
# ---------------------------------------------------------------------------

def _row_label(row: HandRow, board: list[int]) -> str | None:
    if row.label:
        return row.label
    if not board:
        return None
    try:
        combos = [parse_cards(row.hand)] if len(row.hand) == 4 else class_combos(row.hand)
    except (ValueError, IndexError):
        return None
    labels = set()
    for c in combos:
        if c[0] in board or c[1] in board:
            continue
        labels.add(classify_combo(c, board)["label"])
    if len(labels) == 1:
        return labels.pop()
    if labels:
        return "/".join(sorted(labels))
    return None


def outliers_section(ctx: Context, node: Node | None = None, rows: list[HandRow] | None = None) -> Section:
    s = ctx.spot
    node = node or s.node
    rows = rows if rows is not None else s.hands
    if not node or not node.actions or not rows:
        return _uncovered("outliers")
    main = max(node.actions, key=node.actions.get)
    if main.lower().startswith("fold") and node.actions[main] > 50:
        return _outliers_continuing(ctx, node, rows)
    avg = node.actions[main]
    more, less = [], []
    by_label: dict[str, list[float]] = {}
    for r in rows:
        if not r.strategy:
            continue
        f = r.strategy.get(main, 0.0)
        lab = _row_label(r, s.board)
        if lab:
            by_label.setdefault(lab, []).append(f)
        dev = f - avg
        if dev >= 30:
            more.append((dev, r, lab))
        elif dev <= -30:
            less.append((dev, r, lab))
    lines = [f"The range plays **{main}** {pct(avg)} of the time overall. Hands that deviate from that by 30 points or more:"]
    if more:
        lines.append(
            f"- **{main} more often:** "
            + ", ".join(f"{pretty_hand(r.hand)} {pct(r.strategy.get(main, 0))}" + (f" ({lab})" if lab else "") for _, r, lab in sorted(more, key=lambda t: -t[0])[:10])
        )
    if less:
        lines.append(
            f"- **{main} less often:** "
            + ", ".join(f"{pretty_hand(r.hand)} {pct(r.strategy.get(main, 0))}" + (f" ({lab})" if lab else "") for _, r, lab in sorted(less, key=lambda t: t[0])[:10])
        )
    if not more and not less:
        lines.append("- None: hands follow the range strategy closely, so the range-level reason explains them all.")
    facts = {"main_action": main, "range_freq": avg, "more": [r.hand for _, r, _ in more], "less": [r.hand for _, r, _ in less]}
    if len(by_label) >= 2:
        rows_t = sorted(((lab, sum(v) / len(v), len(v)) for lab, v in by_label.items()), key=lambda t: -t[1])
        lines.append("\nAverage by hand type (unweighted across the rows you captured):\n\n" + table(["Hand type", f"{main} %", "Rows"], [[l, pct(a), n] for l, a, n in rows_t]) + "\n")
        facts["by_label"] = {l: a for l, a, _ in rows_t}
        spread = rows_t[0][1] - rows_t[-1][1]
        if spread >= 40:
            lines.append(
                f"The split is driven by hand type: {rows_t[0][0]} plays {main} {pct(rows_t[0][1])} of the time while {rows_t[-1][0]} does it {pct(rows_t[-1][1])}. "
                "Ask what each type gains from the action: value, protection, fold equity, or keeping a share of the pot."
            )
    # Same hand type, different action -> card removal is the usual reason.
    same_type_split = []
    for lab, vals in by_label.items():
        if len(vals) >= 2 and max(vals) - min(vals) >= 60:
            same_type_split.append(lab)
    if same_type_split:
        lines.append(
            "Within " + ", ".join(same_type_split) + " the strategy still splits sharply. When hands of the same strength act differently, "
            "the reason is usually card removal: which opponent hands they block or unblock (see blockers)."
        )
        facts["same_type_split"] = same_type_split
    return Section("outliers", TITLES["outliers"], "\n".join(lines), facts)


def _outliers_continuing(ctx: Context, node: Node, rows: list[HandRow]) -> Section:
    """When most of the range folds, compare hands within the continuing range."""
    fold_key = max(node.actions, key=node.actions.get)
    cont = 100.0 - node.actions[fold_key]
    lines = [
        f"{node.player} folds {pct(node.actions[fold_key])} and continues with {pct(cont)} of hands. "
        "Within the continuing range, each action has its own go-to hands:"
    ]
    facts: dict = {"continuing_pct": cont, "by_action": {}}
    for act, freq in sorted(node.actions.items(), key=lambda kv: -kv[1]):
        if act == fold_key or freq < 1.0:
            continue
        share = 100.0 * freq / cont if cont else 0.0
        picks = [r for r in rows if r.strategy.get(act, 0.0) - share >= 40]
        picks.sort(key=lambda r: -r.strategy.get(act, 0.0))
        facts["by_action"][act] = {"share_of_continues": share, "hands": [r.hand for r in picks]}
        if picks:
            lines.append(
                f"- **{act}** ({pct(share)} of continues): "
                + ", ".join(f"{pretty_hand(r.hand)} {pct(r.strategy.get(act, 0))}" for r in picks[:12])
                + (f" and {len(picks) - 12} more" if len(picks) > 12 else "")
            )
    mixed = [r for r in rows if sum(1 for v in r.strategy.values() if v >= 20) >= 2]
    if mixed:
        lines.append(
            "\nHands that mix between two or more actions (each at least 20%): "
            + ", ".join(pretty_hand(r.hand) for r in mixed[:14])
            + ". Mixed hands sit on the boundary between two actions and have near-equal EVs."
        )
        facts["mixed"] = [r.hand for r in mixed]
    return Section("outliers", TITLES["outliers"], "\n".join(lines), facts)


# ---------------------------------------------------------------------------
# 8. Opponent response
# ---------------------------------------------------------------------------

def response_section(ctx: Context) -> Section:
    s = ctx.spot
    r = s.response
    if not r or not r.actions:
        return _uncovered("response")
    lines = [f"Facing {r.facing or 'the action'}, {r.player} plays: {actions_line(r.actions)}."]
    if r.note:
        lines.append(r.note)
    facts: dict = {"actions": r.actions}
    fold = next((v for a, v in r.actions.items() if a.lower().startswith("fold")), None)
    bet = s.data.get("bet") or {}
    size, pot_before = bet.get("size"), bet.get("pot_before", s.pot)
    if size and pot_before:
        be_fold = 100 * size / (pot_before + size)
        mdf = 100 - be_fold
        facts.update(breakeven_fold=be_fold, mdf=mdf)
        lines.append(
            f"A {size:g}bb bet into {pot_before:g}bb risks {size:g} to win {pot_before:g}: a hand with zero equity needs "
            f"{r.player} to fold {pct(be_fold)} to break even (so the defender's MDF is {pct(mdf)})."
        )
        if fold is not None:
            if fold < be_fold - 10:
                lines.append(
                    f"{r.player} folds only {pct(fold)}, far below {pct(be_fold)}. So the bet can't be profiting as a pure bluff: "
                    "the hands making it must also win money when called, as value, through equity when called, or by keeping their share of a split pot."
                )
                ctx.lesson(
                    7,
                    f"{r.player} folds {pct(fold)}, well short of the {pct(be_fold)} a zero-equity bluff needs, so every hand that bets has to earn when called too.",
                )
            elif fold > be_fold + 10:
                lines.append(f"{r.player} folds {pct(fold)}, more than the {pct(be_fold)} a bluff needs, so even zero-equity hands profit from betting here.")
            else:
                lines.append(f"{r.player} folds {pct(fold)}, close to the {pct(be_fold)} break-even: the bettor's bluffs are near indifferent, as equilibrium predicts.")
    if r.pot_odds is not None:
        po = r.pot_odds * 100 if r.pot_odds <= 1 else r.pot_odds
        facts["pot_odds"] = po
        lines.append(f"{r.player} is getting {pct(po)} pot odds: a call needs at least that much equity in chip EV.")
    if r.hands:
        indiff = [h for h in r.hands if len(h.ev) >= 2 and abs(max(h.ev.values()) - min(h.ev.values())) < 0.5]
        def ev_cell(h: HandRow) -> str:
            if h.ev:
                return ", ".join(f"{a} {v:.2f}" for a, v in h.ev.items())
            return f"{h.ev_best:.2f}" if h.ev_best is not None else "–"

        has_eq = any(h.equity is not None for h in r.hands)
        has_note = any(h.label for h in r.hands)
        headers = ["Hand", "Strategy", "EV (bb)"] + (["Equity"] if has_eq else []) + (["Note"] if has_note else [])
        rows = []
        for h in r.hands[:24]:
            row = [pretty_hand(h.hand), actions_line(h.strategy), ev_cell(h)]
            if has_eq:
                row.append(pct(h.equity) if h.equity is not None else "–")
            if has_note:
                row.append(h.label or "")
            rows.append(row)
        lines.append(table(headers, rows))
        if not has_eq:
            lines.append("_No equities captured for these rows; add `equity` (EQ % column) to explain which calls are thin._")
        if indiff:
            lines.append(
                "Near-indifferent hands (EV gap under 0.5bb): " + ", ".join(pretty_hand(h.hand) for h in indiff[:8])
                + ". These are the bluff-catchers that set the bettor's ratio of value to bluffs."
            )
        eq_rows = [h for h in r.hands if h.equity is not None]
        if eq_rows and r.pot_odds is not None:
            po = r.pot_odds * 100 if r.pot_odds <= 1 else r.pot_odds
            thin = [h for h in eq_rows if 0 <= h.equity - po < 3]
            if thin:
                lines.append(
                    "Calls that barely clear the price: "
                    + ", ".join(f"{pretty_hand(h.hand)} ({pct(h.equity)} vs {pct(po)} needed)" for h in thin[:6])
                    + ". Under ICM these are the first calls to become folds."
                )
    if r.breakdown:
        rows = [[c.get("category"), pct(c.get("pct")), f1(c.get("combos")), actions_line(c.get("strategy", {}))] for c in r.breakdown]
        lines.append(f"**{r.player}'s range facing it:**\n\n" + table(["Category", "Range %", "Combos", "Strategy"], rows))
    return Section("response", TITLES["response"], "\n\n".join(lines), facts)


# ---------------------------------------------------------------------------
# 9. Alternative line
# ---------------------------------------------------------------------------

def alternatives_section(ctx: Context) -> Section:
    s = ctx.spot
    if not s.alternatives:
        return _uncovered("alternatives")
    lines = []
    facts = []
    inference = False
    for alt in s.alternatives:
        steps = [Node.from_dict(st) for st in alt.get("steps", [])]
        steps = [st for st in steps if st]
        desc = [f"**If {alt.get('line', 'the other line')}:**"]
        for st in steps:
            facing = f" facing {st.facing}" if st.facing else ""
            desc.append(f"- {st.player}{facing}: {actions_line(st.actions)}" + (f". {st.note}" if st.note else ""))
        if alt.get("note"):
            desc.append(alt["note"])
        # Pattern: opponent shoves a lot, then the original player folds a lot.
        shove_step = next((st for st in steps if any(is_allin(a) and v >= 40 for a, v in st.actions.items())), None)
        if shove_step:
            later = steps[steps.index(shove_step) + 1 :]
            fold_step = next((st for st in later if st.player != shove_step.player and st.actions.get("Fold", 0) >= 50), None)
            if fold_step:
                shove_pct = max(v for a, v in shove_step.actions.items() if is_allin(a))
                fold_pct = fold_step.actions["Fold"]
                desc.append(
                    f"So on this line {shove_step.player} takes the initiative: it shoves {pct(shove_pct)} and "
                    f"{fold_step.player} then folds {pct(fold_pct)}, giving up its share of the pot with every hand that folds. "
                    "Comparing the lines shows the value of acting first: the player who moves all-in puts the other one to the hard decision."
                )
                inference = True
                ctx.lesson(
                    9,
                    f"Betting first matters here: after the other line {shove_step.player} shoves {pct(shove_pct)} and {fold_step.player} folds {pct(fold_pct)}, "
                    "so hands that check give up the share of the pot they would keep by shoving.",
                )
        # Same opponent, two lines: compare how often it folds.
        resp = s.response
        if resp and steps and steps[0].player == resp.player:
            f_main = next((v for a, v in resp.actions.items() if a.lower().startswith("fold")), None)
            f_alt = next((v for a, v in steps[0].actions.items() if a.lower().startswith("fold")), None)
            if f_main is not None and f_alt is not None and abs(f_main - f_alt) >= 15:
                better = "the main line" if f_main > f_alt else "this line"
                desc.append(
                    f"{resp.player} folds {pct(f_main)} to the main line but {pct(f_alt)} here, so {better} gets {resp.player} to fold far more often. "
                    "Both numbers are conditional on the action reaching that node (e.g. other players folding first)."
                )
                aggr_parts = {a: v for a, v in steps[0].actions.items() if (is_allin(a) or "raise" in a.lower()) and v > 0}
                aggr_alt = sum(aggr_parts.values())
                main_name = re.sub(r"\s*\(.*\)", "", resp.facing or "main action")
                alt_name = re.sub(r"\s*\(.*\)", "", steps[0].facing or alt.get("line", "other line"))
                ctx.lesson(
                    8,
                    f"{resp.player} folds {pct(f_main)} to {main_name} but only {pct(f_alt)} to {alt_name}"
                    + (
                        f", and re-raises {pct(aggr_alt)} against it ({' + '.join(f'{a} {pct(v)}' for a, v in aggr_parts.items())})"
                        if aggr_alt >= 10
                        else ""
                    )
                    + ": choosing between the two is mostly about how often you win the pot without a fight.",
                )
        facts.append({"line": alt.get("line"), "action": alt.get("action"), "steps": [st.__dict__ for st in steps]})
        lines.append("\n".join(desc))
    sec = Section("alternatives", TITLES["alternatives"], "\n\n".join(lines), {"alternatives": facts}, inference=inference)
    # Which of the hero's other actions have no captured line?
    uncaptured = _uncaptured_actions(s)
    if uncaptured:
        sec.facts["uncaptured_actions"] = uncaptured
        sec.partial = (
            "No line captured after " + ", ".join(uncaptured)
            + ". Any reason given for not choosing it is inference; capture the node after it to explain it from the data."
        )
    return sec


_ACTION_WORDS = {
    "check": ("check",),
    "call": ("call", "flat", "limp"),
    "fold": ("fold",),
    "raise": ("raise", "3-bet", "3bet", "4-bet", "4bet", "squeeze", "min-raise"),
    "bet": ("bet", "lead", "c-bet", "cbet"),
    "allin": ("allin", "all-in", "all in", "jam", "shove"),
}


def _action_kind(action: str) -> str:
    a = action.lower()
    if is_allin(a):
        return "allin"
    for kind in ("check", "call", "fold", "raise", "bet"):
        if a.startswith(kind):
            return kind
    return a.split()[0] if a.split() else a


def _uncaptured_actions(s: Spot) -> list[str]:
    """Actions the hero's range uses (>=1%, not fold, not the main one) with no alternative line."""
    node = s.node
    if not node or not node.actions:
        return []
    main = s.response.facing if s.response and s.response.facing else None
    used = [a for a, v in node.actions.items() if v >= 1.0 and not a.lower().startswith("fold")]
    if main:
        main_kind = _action_kind(main)
        used = [a for a in used if not (a == main or (_action_kind(a) == main_kind and main.split()[0] in a))]
    captured_text = []
    for alt in s.alternatives:
        if alt.get("action"):
            captured_text.append(str(alt["action"]).lower())
        captured_text.append(str(alt.get("line", "")).lower())
    out = []
    for a in used:
        al = a.lower()
        if any(al == t or al.split(" (")[0] == t for t in captured_text):
            continue
        kind = _action_kind(a)
        words = _ACTION_WORDS.get(kind, (kind,))
        if any(any(w in t for w in words) for t in captured_text):
            continue
        out.append(a)
    return out


# ---------------------------------------------------------------------------
# 10. Rewind
# ---------------------------------------------------------------------------

def rewind_section(ctx: Context) -> Section:
    rw = ctx.spot.rewind
    if not rw or not rw.get("rows"):
        return _uncovered("rewind")
    steps: list[str] = rw.get("steps", [])
    player = rw.get("player", "the player")
    rows_out = []
    lost_by_step = [0.0] * len(steps)
    reach_total = 0.0
    checks = []
    for row in rw["rows"]:
        freqs = normalise_freq_list(row["freqs"])
        reach = 1.0
        for i, f in enumerate(freqs):
            if i < len(lost_by_step):
                lost_by_step[i] += reach * (1 - f)
            reach *= f
        reach_total += reach
        worst = min(range(len(freqs)), key=lambda i: freqs[i]) if freqs else None
        observed = row.get("weight")
        if observed is not None and abs(observed - reach) > 0.05:
            checks.append((row["hand"], reach, observed))
        rows_out.append(
            [
                pretty_hand(row["hand"]),
                row.get("label", ""),
                *[pct(100 * f) for f in freqs],
                f"{100 * reach:.0f}%",
                f2(observed) if observed is not None else "–",
                steps[worst] if worst is not None and worst < len(steps) and freqs[worst] < 0.6 else "–",
            ]
        )
    lines = [
        f"Every weight in {player}'s range is the product of how often each combo took this line on earlier streets. "
        "Multiplying the street frequencies shows which street removed which hands:",
        table(["Combo", "Type", *steps, "Reaches", "Weight seen", "Filtered by"], rows_out),
    ]
    if any(lost_by_step):
        i = max(range(len(steps)), key=lambda k: lost_by_step[k])
        lines.append(
            f"Across these combos, **{steps[i]}** removed the most weight ({lost_by_step[i]:.1f} of the {len(rw['rows'])} combos listed). "
            "Hands that left the line there show up in a different branch of the tree, not in this river range."
        )
        ctx.lesson(5, f"{player}'s range here is filtered: {steps[i]} removed most of the hands that would otherwise be at the top of it.")
    if checks:
        lines.append(
            "Product and observed weight differ for: "
            + ", ".join(f"{pretty_hand(h)} ({100 * a:.0f}% vs {o:.2f})" for h, a, o in checks)
            + ". The usual cause is the preflop step (the hand is only partly in the opening range) if it isn't in the list."
        )
    return Section("rewind", TITLES["rewind"], "\n\n".join(lines), {"lost_by_step": dict(zip(steps, lost_by_step))})


# ---------------------------------------------------------------------------
# 11. Blockers
# ---------------------------------------------------------------------------

def blockers_section(ctx: Context) -> Section:
    s = ctx.spot
    lines: list[str] = []
    facts: dict = {}
    hero = s.hero_hand.hand if s.hero_hand else None
    vr = s.ranges.get(s.villain)
    if hero and len(hero) == 4 and vr is not None and s.board:
        hc = parse_cards(hero)
        rep = [r for r in blocker_report(hc, vr, s.board) if r["before"] > 0]
        moved = [r for r in rep if r["removed_pct"] > 0]
        facts["groups"] = rep
        if moved:
            lines.append(
                f"{pretty_hand(hero)} removes these {s.villain} combos:\n\n"
                + table(["Group", "Combos before", "After", "Removed"], [[r["group"], r["before"], r["after"], pct(r["removed_pct"])] for r in moved])
            )
        else:
            lines.append(f"{pretty_hand(hero)} doesn't remove any of {s.villain}'s combos in the range you supplied.")
        if s.villain in s.partial_ranges:
            lines.append(f"(The {s.villain} range supplied is partial, so the table only covers the combos you listed.)")
        if len(s.board) == 5 and s.villain not in s.partial_ranges:
            base = showdown_split(hc, vr, s.board)  # removes board and hero cards
            tot = base["total"] or 1
            facts["split"] = base
            lines.append(
                f"Against {s.villain}'s remaining range, {pretty_hand(hero)} loses to {pct(100 * base['beats_hero'] / tot)}, "
                f"chops with {pct(100 * base['chops'] / tot)} and beats {pct(100 * base['hero_beats'] / tot)}."
            )
            strong = [r for r in rep if r["group"] not in ("Plays the board",) and r["removed_pct"] >= 30]
            if strong:
                ctx.lesson(
                    4,
                    f"{pretty_hand(hero)} blocks a big part of {s.villain}'s strongest hands ({', '.join(r['group'] for r in strong)}), which is what makes it a good hand for this action.",
                )
    if s.board and len(s.board) == 5 and hero and len(hero) == 4:
        bb = board_beaters(s.board)
        held = [c for c in parse_cards(hero) if c in bb.single_card_outs]
        if held:
            lines.append(
                f"{pretty_hand(hero)} holds {', '.join(card_str(c, True) for c in held)}, one of the only cards that beat the board, "
                f"so {s.villain} can't hold it."
            )
    if s.blockers_tab:
        bt = s.blockers_tab
        lines.append(
            "GTO Wizard Blockers tab: "
            + ", ".join(f"{k.replace('_', ' ')} {v}" for k, v in bt.items())
            + ". Value removal counts how many of the opponent's strong hands you block; trash removal counts the weak ones."
        )
        facts["blockers_tab"] = bt
    if not lines:
        return _uncovered("blockers")
    return Section("blockers", TITLES["blockers"], "\n\n".join(lines), facts)


# ---------------------------------------------------------------------------
# 12. ICM
# ---------------------------------------------------------------------------

def _icm_stacks(s: Spot) -> tuple[list[float], list[float]] | None:
    pays = s.format.get("payouts")
    if not pays or not s.table:
        return None
    stacks = s.start_stacks()
    if s.format.get("players_left") and s.format.get("average_stack"):
        stacks = icm_mod.pad_with_field(stacks, int(s.format["players_left"]), float(s.format["average_stack"]))
    return stacks, [float(p) for p in pays]


def icm_section(ctx: Context) -> Section:
    s = ctx.spot
    lines: list[str] = []
    facts: dict = {}
    inference = False
    if s.icm_compare:
        ic = s.icm_compare
        chip = {k: v for k, v in (ic.get("chipev") or {}).items()}
        icm_ = {k: v for k, v in (ic.get("icm") or {}).items()}
        from .spot import normalise_actions

        chip, icm_ = normalise_actions(chip), normalise_actions(icm_)
        acts = sorted(set(chip) | set(icm_))
        rows = [[a, pct(chip.get(a)), pct(icm_.get(a)), f"{icm_.get(a, 0) - chip.get(a, 0):+.1f}"] for a in acts]
        lines.append(f"Same spot solved both ways ({ic.get('player', s.node.player if s.node else '')}):\n\n" + table(["Action", "ChipEV", "ICM", "Change"], rows))
        biggest = max(acts, key=lambda a: abs(icm_.get(a, 0) - chip.get(a, 0)))
        lines.append(f"The biggest shift is {biggest} ({icm_.get(biggest, 0) - chip.get(biggest, 0):+.1f} points). " + (ic.get("note") or ""))
        facts["compare"] = {"chipev": chip, "icm": icm_}
    stacks_pays = _icm_stacks(s)
    hi, vi = s.seat_index(s.hero), s.seat_index(s.villain)
    if stacks_pays and hi is not None and vi is not None:
        stacks, pays = stacks_pays
        bf_hv = icm_mod.bubble_factor(stacks, pays, hi, vi)
        bf_vh = icm_mod.bubble_factor(stacks, pays, vi, hi)
        facts.update(bubble_factor={f"{s.hero} vs {s.villain}": bf_hv, f"{s.villain} vs {s.hero}": bf_vh})
        lines.append(
            "Bubble factors (start-of-hand stacks, Malmuth-Harville ICM):\n\n"
            + table(
                ["Risking chips", "Against", "Bubble factor", "Meaning"],
                [[s.hero, s.villain, f2(bf_hv), icm_mod.describe_bubble_factor(bf_hv)], [s.villain, s.hero, f2(bf_vh), icm_mod.describe_bubble_factor(bf_vh)]],
            )
        )
        lines.append(
            "A bubble factor of 1.5 means losing a chip costs 1.5 times what winning one gains. "
            f"The player with the higher number ({s.hero if bf_hv > bf_vh else s.villain}) has to be more careful in a big pot between these two."
        )
        # Facing an all-in: whose decision?
        pairs = []
        if s.response and s.response.facing and is_allin(s.response.facing):
            pairs.append((s.villain, s.hero))  # villain calls hero's shove
        if s.node and s.node.facing and is_allin(s.node.facing):
            pairs.append((s.hero, s.villain))
        for caller, shover in pairs:
            ci, si = s.seat_index(caller), s.seat_index(shover)
            cc = s.committed(caller) or 0.0
            sc = s.committed(shover) or 0.0
            dead = max(0.0, (s.pot or 0.0) - cc - sc)
            m = icm_mod.allin_call_requirements(stacks, pays, ci, si, hero_committed=cc, villain_committed=s.start_stack(shover), dead_money=dead)
            facts[f"{caller}_call"] = {"chip_required": m.chip_required, "icm_required": m.icm_required, "risk_premium": m.risk_premium}
            lines.append(
                f"**{caller} calling {shover}'s all-in:** chip EV needs {pct(100 * m.chip_required)} equity; with ICM it needs "
                f"{pct(100 * m.icm_required)}. The difference, {pct(100 * m.risk_premium)}, is {caller}'s risk premium."
            )
            if m.risk_premium > 0.03:
                ctx.lesson(8, f"ICM adds a {100 * m.risk_premium:.1f}% risk premium to {caller}'s call, which is why the all-in gets through more often than chip EV would allow.")
        if s.format.get("players_left") and s.format.get("average_stack"):
            ctx.spot.data.setdefault("_warnings", []).append(
                "ICM numbers model the rest of the field as average stacks; GTO Wizard uses the real ladder, so treat them as directional."
            )
    elif s.format.get("icm"):
        hb = s.behind(s.hero) or s.start_stack(s.hero)
        vb = s.behind(s.villain) or s.start_stack(s.villain)
        if hb is not None and vb is not None:
            covered = s.hero if hb < vb else s.villain
            covering = s.villain if covered == s.hero else s.hero
            lines.append(
                f"The solution uses ICM. {covering} covers {covered}, so in an all-in only {covered} risks busting. "
                f"Under ICM that makes {covered}'s losses heavier than its wins: {covered} needs more equity to call off, "
                f"and {covering} can apply pressure with hands that would be too weak in chip EV."
            )
            inference = True
            facts["qualitative_only"] = True
    if not lines:
        return _uncovered("icm")
    sec = Section("icm", TITLES["icm"], "\n\n".join(lines), facts, inference=inference)
    if facts.get("qualitative_only"):
        sec.partial = "Qualitative only. Add the payout ladder (`format.payouts`) for bubble factors and the risk premium, or capture the same node solved in ChipEV (`icm_compare`)."
    return sec


# ---------------------------------------------------------------------------
# 13. Lesson
# ---------------------------------------------------------------------------

def lesson_section(ctx: Context) -> Section:
    s = ctx.spot
    if s.lesson:
        text = s.lesson
    elif ctx.lessons:
        text = max(ctx.lessons, key=lambda t: t[0])[1]
    else:
        text = "Capture the opponent's response and the alternative line to find the lesson; the range strategy alone rarely explains why."
    others = [t for p, t in sorted(ctx.lessons, key=lambda t: -t[0]) if t != text][:2]
    body = f"**{text}**"
    if others:
        body += "\n\nAlso worth remembering:\n" + "\n".join(f"- {o}" for o in others)
    if s.notes:
        body += "\n\nNotes:\n" + "\n".join(f"- {n}" for n in s.notes)
    return Section("lesson", TITLES["lesson"], body, {"lesson": text})
