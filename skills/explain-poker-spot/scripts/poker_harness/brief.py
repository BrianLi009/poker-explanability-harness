"""Hand an explanation job to an LLM, and check what comes back.

``build_brief`` packs the computed facts and the coaching framework into a
prompt. ``check_explanation`` is a lightweight rubric: it flags framework
points the explanation skipped and key numbers it never mentions, which is
how you catch the most common failure (explaining a bet without looking at
the opponent's response).
"""

from __future__ import annotations

import json
import re
from pathlib import Path

from .framework import CHECKLIST, Report

PROMPT_PATH = Path(__file__).with_name("prompts") / "explain_hand.md"


def build_brief(report: Report) -> str:
    template = PROMPT_PATH.read_text()
    facts = report.to_dict()
    # Keep the brief compact: bodies are for humans, facts are for the model.
    compact = {
        "title": facts["title"],
        "module": facts["module"],
        "source": facts["source"],
        "sections": [
            {"key": s["key"], "title": s["title"], "facts": s["facts"], "draft": s["body"], "inference": s["inference"], "partial": s["partial"]}
            for s in facts["sections"]
            if s["covered"]
        ],
        "missing": [c["title"] for c in facts["coverage"] if c["status"] == "missing"],
        "partial": {c["title"]: c["note"] for c in facts["coverage"] if c["status"] == "partial"},
        "warnings": facts["warnings"],
    }
    checklist = "\n".join(f"{i + 1}. **{t}** ({k})" for i, (k, t, _) in enumerate(CHECKLIST))
    return template.replace("{{CHECKLIST}}", checklist).replace("{{FACTS}}", json.dumps(compact, indent=2, default=str))


def _numbers(text: str) -> set[str]:
    return set(re.findall(r"\d+(?:\.\d+)?", text))


def key_numbers(report: Report) -> dict[str, list[str]]:
    """Numbers each covered section should surface in a good explanation."""
    out: dict[str, list[str]] = {}
    for s in report.sections:
        if not s.covered:
            continue
        f = s.facts
        nums: list[float] = []
        if s.key == "response":
            nums += list(f.get("actions", {}).values())
        elif s.key == "range_first":
            nums += [v for v in f.get("actions", {}).values() if v >= 1]
        elif s.key == "alternatives":
            for alt in f.get("alternatives", []):
                for st in alt.get("steps", []):
                    acts = st.get("actions", {})
                    if acts:
                        nums.append(max(acts.values()))
        elif s.key == "icm":
            for k, v in f.items():
                if k.endswith("_call"):
                    nums += [100 * v["chip_required"], 100 * v["icm_required"]]
        elif s.key == "hero_hand" and "ev_gap" in f:
            nums.append(f["ev_gap"])
        if nums:
            out[s.key] = [f"{n:.1f}" if abs(n) >= 1 else f"{n:.2f}" for n in nums]
    return out


def _known_numbers(report: Report) -> set[float]:
    """Every number the report states or computes, for spotting invented figures."""
    text = report.to_markdown() + json.dumps(report.to_dict(), default=str)
    return {float(n) for n in re.findall(r"\d+(?:\.\d+)?", text)}


def _close(x: float, known: set[float]) -> bool:
    return any(abs(x - k) <= 0.051 for k in known)


def check_explanation(text: str, report: Report, source: dict | None = None) -> dict:
    """Lint a written explanation against the report.

    This is a coverage lint, not a correctness check: it can't tell a right
    claim from a wrong one. It reports
      * missing_points: covered framework points the text never touches,
      * missing_numbers: sections where under half the key numbers appear,
      * unsupported_numbers: percentages / bb figures that appear nowhere in
        the report or the spot data (likely invented or mis-copied),
      * too_short: under 150 words for a multi-point report.
    """
    lowered = text.lower()
    present_nums = _numbers(text)
    hints = {
        "response": ["call", "fold", "respond", "response"],
        "alternatives": ["instead", "if we check", "checks", "other line", "alternative", "small 3-bet", "3-bet", "if you"],
        "rewind": ["flop", "turn", "earlier street", "got here", "filtered"],
        "blockers": ["block", "removal", "remove"],
        "icm": ["icm", "bubble", "risk premium", "covers", "bust"],
        "outliers": ["outlier", "while", "whereas", "instead of", "unlike"],
    }
    missing_points = []
    for key, words in hints.items():
        sec = report.get(key)
        if sec and sec.covered and not any(w in lowered for w in words):
            missing_points.append(key)
    # Lesson: a labelled takeaway, or a short closing paragraph.
    paras = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]
    last = paras[-1] if paras else ""
    has_lesson = any(w in lowered for w in ("lesson", "takeaway", "remember", "rule of thumb", "at the table")) or (
        0 < len(last.split()) <= 45 and len(paras) >= 3
    )
    if report.get("lesson") and not has_lesson:
        missing_points.append("lesson")

    missing_numbers = {}
    keys = key_numbers(report)
    present_frac = []
    for key, nums in keys.items():
        found = [n for n in nums if n in present_nums or n.rstrip("0").rstrip(".") in present_nums]
        present_frac.append(len(found) / len(nums))
        if len(found) * 2 < len(nums):
            missing_numbers[key] = [n for n in nums if n not in found]

    known = _known_numbers(report)
    if source is not None:
        known |= {float(n) for n in re.findall(r"\d+(?:\.\d+)?", json.dumps(source, default=str))}
    stated = re.findall(r"(\d+(?:\.\d+)?)\s*(%|bb)", text)
    unsupported = sorted({f"{n}{u}" for n, u in stated if not _close(float(n), known)})

    words = len(text.split())
    too_short = words < 150 and sum(1 for s in report.sections if s.covered) >= 6

    score = 1.0
    score -= 0.35 * len(missing_points) / (len(hints) + 1)
    if present_frac:
        score -= 0.35 * (1 - sum(present_frac) / len(present_frac))
    score -= min(0.2, 0.05 * len(unsupported))
    if too_short:
        score = min(score, 0.5)
    return {
        "score": round(max(0.0, score), 2),
        "missing_points": missing_points,
        "missing_numbers": missing_numbers,
        "unsupported_numbers": unsupported,
        "too_short": too_short,
        "words": words,
        "note": "Coverage lint only: it can't verify that claims are correct. Reread blocker and line claims against the report.",
    }
