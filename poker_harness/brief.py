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
            {"key": s["key"], "title": s["title"], "facts": s["facts"], "draft": s["body"], "inference": s["inference"]}
            for s in facts["sections"]
            if s["covered"]
        ],
        "missing": [c["title"] for c in facts["coverage"] if not c["covered"]],
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


def check_explanation(text: str, report: Report) -> dict:
    """Which framework points and key numbers a written explanation misses."""
    lowered = text.lower()
    present_nums = _numbers(text)
    hints = {
        "response": ["call", "fold", "respond", "response"],
        "alternatives": ["instead", "if we check", "if sb checks", "other line", "alternative"],
        "rewind": ["flop", "turn", "earlier street", "got here"],
        "blockers": ["block", "removal", "remove"],
        "icm": ["icm", "bubble", "risk premium", "covers"],
        "outliers": ["outlier", "while", "whereas", "instead of"],
        "lesson": ["lesson", "takeaway", "remember"],
    }
    missing_points = []
    for key, words in hints.items():
        sec = report.get(key)
        if sec and sec.covered and not any(w in lowered for w in words):
            missing_points.append(key)
    missing_numbers = {}
    for key, nums in key_numbers(report).items():
        absent = [n for n in nums if n not in present_nums and n.rstrip("0").rstrip(".") not in present_nums]
        if absent and len(absent) == len(nums):
            missing_numbers[key] = absent
    score = 1.0
    covered = [s for s in report.sections if s.covered]
    if covered:
        score -= 0.5 * len(missing_points) / max(1, len(hints))
        score -= 0.5 * len(missing_numbers) / max(1, len(key_numbers(report)) or 1)
    return {"score": round(max(0.0, score), 2), "missing_points": missing_points, "missing_numbers": missing_numbers}
