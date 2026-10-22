"""The explanation framework: what a good hand breakdown covers.

The checklist distils how strong coaches (GTO Wizard's hand analyses,
Kevin Rabichow, Carrot Corner, Octopi's Vault, GTO LAB) walk through a
spot. Every report the harness produces is organised by these keys, and
the coverage table at the end shows which ones the captured data could
support and what to grab from GTO Wizard to fill the gaps.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from typing import Any

CHECKLIST: list[tuple[str, str, str]] = [
    ("decision", "Judge the decision, not the result", "Always covered."),
    ("scene", "Set the scene", "Table stacks, positions, pot and format (GTO Wizard header / URL)."),
    ("board", "Read the board", "Board cards (postflop only)."),
    ("ranges", "Shape of both ranges", "Breakdown tab and Equity chart for both players, or the Ranges tab."),
    ("range_first", "What the whole range does", "Overview actions with frequencies and combos."),
    ("hero_hand", "Where the hand sits and its EV", "Strategy + EV for the hand (Hands tab or Summary)."),
    ("outliers", "Outlier hands and why", "Per-hand strategy rows (Summary tab or grid)."),
    ("response", "The opponent's response", "The next node: the opponent's actions facing your action."),
    ("alternatives", "What happens on the other line", "The node after your other main action (e.g. after a check)."),
    ("rewind", "How the ranges got here", "Earlier-street frequencies for the key combos."),
    ("blockers", "Blockers and card removal", "Opponent range (to count combos) or the Blockers tab."),
    ("icm", "ICM versus chip EV", "Payouts and stacks, or the same spot solved in ChipEV."),
    ("lesson", "One-sentence takeaway", "Always covered."),
]

CHECKLIST_KEYS = [k for k, _, _ in CHECKLIST]
TITLES = {k: t for k, t, _ in CHECKLIST}
WHAT_TO_CAPTURE = {k: c for k, _, c in CHECKLIST}


@dataclass
class Section:
    key: str
    title: str
    body: str = ""
    facts: dict[str, Any] = field(default_factory=dict)
    covered: bool = True
    inference: bool = False  # True when the section reasons beyond the solver output
    partial: str | None = None  # set when covered from thin data: says what's missing

    def markdown(self) -> str:
        head = f"## {self.title}"
        tags = []
        if self.inference:
            tags.append("includes inference")
        if self.partial:
            tags.append("partial")
        if tags:
            head += f" *({', '.join(tags)})*"
        body = self.body.strip()
        if self.partial:
            body += f"\n\n_Partial: {self.partial}_"
        return f"{head}\n\n{body}\n"


@dataclass
class Report:
    title: str
    module: str
    sections: list[Section] = field(default_factory=list)
    source: str | None = None
    warnings: list[str] = field(default_factory=list)

    def get(self, key: str) -> Section | None:
        for s in self.sections:
            if s.key == key:
                return s
        return None

    def add(self, section: Section | None) -> None:
        if section is not None:
            self.sections.append(section)

    def ordered(self) -> list[Section]:
        order = {k: i for i, k in enumerate(CHECKLIST_KEYS)}
        return sorted(self.sections, key=lambda s: order.get(s.key, 99))

    # -- rendering ------------------------------------------------------
    def coverage(self) -> list[dict]:
        """One row per framework point: status is covered, partial, missing or n/a."""
        rows = []
        for key, title, capture in CHECKLIST:
            s = self.get(key)
            covered = bool(s and s.covered)
            if self.module == "preflop" and key == "board":
                status, note = "n/a", "No board preflop."
            elif self.module == "preflop" and key == "rewind" and not covered:
                status, note = "n/a", "Earlier folds rarely filter a preflop range; capture only for later preflop nodes."
            elif covered and s.partial:
                status, note = "partial", s.partial
            elif covered:
                status, note = "covered", None
            else:
                status, note = "missing", capture
            rows.append({"key": key, "title": title, "status": status, "covered": status in ("covered", "partial"), "to_capture": note if status in ("partial", "missing") else None, "note": note})
        return rows

    def to_markdown(self) -> str:
        out = [f"# {self.title}\n"]
        if self.source:
            out.append(f"_Source: {self.source}_\n")
        for s in self.ordered():
            if s.covered:
                out.append(s.markdown())
        cov = self.coverage()
        counts = {k: sum(r["status"] == k for r in cov) for k in ("covered", "partial", "missing", "n/a")}
        out.append("## Coverage\n")
        out.append(
            f"Of the {len(cov)} framework points: {counts['covered']} covered, {counts['partial']} partial, "
            f"{counts['missing']} missing, {counts['n/a']} not applicable.\n"
        )
        todo = [r for r in cov if r["status"] in ("partial", "missing")]
        if todo:
            out.append("To complete the explanation, capture from GTO Wizard:\n")
            for r in todo:
                out.append(f"- **{r['title']}** ({r['status']}): {r['to_capture']}")
            out.append("")
        if self.warnings:
            out.append("## Data warnings\n")
            out += [f"- {w}" for w in self.warnings]
            out.append("")
        return "\n".join(out).rstrip() + "\n"

    def to_dict(self) -> dict:
        return {
            "title": self.title,
            "module": self.module,
            "source": self.source,
            "sections": [asdict(s) for s in self.ordered()],
            "coverage": self.coverage(),
            "warnings": self.warnings,
        }

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent, default=_json_default)


def _json_default(o: Any):
    if isinstance(o, float) and (o != o or o in (float("inf"), float("-inf"))):
        return str(o)
    if hasattr(o, "__dict__"):
        return o.__dict__
    return str(o)
