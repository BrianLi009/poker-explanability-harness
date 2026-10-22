import json
from pathlib import Path

import pytest

from poker_harness import explain, load_spot, validate
from poker_harness.brief import build_brief, check_explanation
from poker_harness.cli import main

EX = Path(__file__).resolve().parent.parent / "skills" / "explain-poker-spot" / "examples"
RIVER = EX / "river_five_flush_shove.json"
PREFLOP = EX / "preflop_sb_vs_lj_open.json"


def test_examples_validate():
    for p in (RIVER, PREFLOP):
        assert validate(load_spot(p)) == []


def test_river_report_covers_everything():
    rep = explain(RIVER)
    cov = rep.coverage()
    assert all(r["covered"] for r in cov), [r for r in cov if not r["covered"]]
    md = rep.to_markdown()
    # Board reading: only four cards beat a five-spade board.
    assert "Only 4 specific cards beat the board" in md
    # Response: a zero-equity shove needs 67.5% folds, LJ folds 16.3%.
    resp = rep.get("response")
    assert resp.facts["breakeven_fold"] == pytest.approx(67.47, abs=0.05)
    # Rewind: flop check removed the most weight.
    assert max(rep.get("rewind").facts["lost_by_step"].items(), key=lambda kv: kv[1])[0] == "Flop check"
    # Lesson comes from the alternative line (check -> LJ shoves -> SB folds).
    assert "LJ shoves 73.1%" in rep.get("lesson").facts["lesson"]


def test_river_blockers_count_flush_removal():
    rep = explain(RIVER)
    groups = {g["group"]: g for g in rep.get("blockers").facts["groups"]}
    assert groups["Straight flush"]["removed_pct"] == 100.0
    assert groups["Flush"]["before"] == pytest.approx(16.35, abs=0.01)


def test_preflop_report_matches_gto_wizard_fold_frequency():
    rep = explain(PREFLOP)
    facts = rep.get("blockers").facts
    # The class rows reproduce GTO Wizard's 69.4% LJ fold frequency exactly.
    assert facts["fold_before"] == pytest.approx(69.41, abs=0.05)
    assert facts["cont_removed_pct"] > facts["fold_removed_pct"]


def test_preflop_outliers_and_family_patterns():
    rep = explain(PREFLOP)
    out = rep.get("outliers")
    assert "Allin 25" in out.facts["by_action"]
    assert "AQo" in out.facts["by_action"]["Allin 25"]["hands"]
    md = rep.to_markdown()
    assert "Hand-family patterns" in md and "KJs" in md


def test_icm_numbers_when_payouts_given():
    data = json.loads(PREFLOP.read_text())
    data["format"]["payouts"] = [30, 20, 14, 10, 8, 6, 5, 4, 3]
    data["stacks_behind"] = {"SB": 24.5, "LJ": 40.0}
    data["node"]["facing"] = None
    rep = explain(data)
    icm = rep.get("icm")
    assert icm.covered and not icm.inference
    bf = icm.facts["bubble_factor"]
    assert bf["SB vs LJ"] > 1.0
    assert "LJ_call" in icm.facts  # LJ facing SB's all-in
    call = icm.facts["LJ_call"]
    assert call["icm_required"] > call["chip_required"]


def test_brief_and_check():
    rep = explain(RIVER)
    brief = build_brief(rep)
    assert "Never explain a bet without the opponent's response" in brief
    assert '"key": "response"' in brief
    bad = "SB shoves 54.5% because the chop hands fold out LJ's chops."
    good = (
        "SB shoves 54.5%. LJ calls 83.7% and folds 16.3%, so it isn't a bluff. If SB checks instead, LJ shoves 73.1% "
        "and SB folds 75.5%. On the flop and turn LJ's flushes were filtered. A♠ blocks the nuts. ICM: LJ covers SB. "
        "Lesson: shove first. Outliers: small pairs shove while KQ checks."
    )
    assert check_explanation(bad, rep)["score"] < check_explanation(good, rep)["score"]
    res = check_explanation(bad, rep)
    assert "response" in res["missing_numbers"]  # never states how LJ responds
    assert "alternatives" in res["missing_points"]


def test_cli(tmp_path, capsys):
    out = tmp_path / "r.md"
    assert main(["explain", str(RIVER), "-o", str(out)]) == 0
    assert out.read_text().startswith("# SB river shove")
    assert main(["explain", str(PREFLOP), "--format", "json"]) == 0
    assert json.loads(capsys.readouterr().out)["module"] == "preflop"
    assert main(["board", "KsJs6s8sQs"]) == 0
    assert main(["validate", str(RIVER)]) == 0


def test_missing_data_reports_what_to_capture():
    rep = explain({"module": "postflop", "board": "AhKd7c", "title": "bare"})
    md = rep.to_markdown()
    assert "To complete the explanation" in md
    assert "The opponent's response" in md


def test_coverage_statuses_preflop():
    cov = {r["key"]: r for r in explain(PREFLOP).coverage()}
    assert len(cov) == 13
    assert cov["board"]["status"] == "n/a" and cov["rewind"]["status"] == "n/a"
    assert cov["ranges"]["status"] == "partial"  # only range widths captured
    assert cov["icm"]["status"] == "partial"  # no payouts
    assert cov["alternatives"]["status"] == "partial"
    assert "Call" in cov["alternatives"]["note"]  # the call line isn't captured


def test_alternatives_full_when_every_action_captured():
    data = json.loads(PREFLOP.read_text())
    data["alternatives"].append({"action": "Call", "line": "SB flats", "steps": [{"player": "BB", "actions": {"Fold": 80, "Raise 9": 20}}]})
    cov = {r["key"]: r for r in explain(data).coverage()}
    assert cov["alternatives"]["status"] == "covered"


def test_preflop_fold_check_and_neighbour_comparison():
    rep = explain(PREFLOP)
    blk = rep.get("blockers")
    assert "matching GTO Wizard's 69.4%" in blk.body
    assert set(blk.facts["compare"]) == {"A4s", "A5s", "A3s"}
    # Missing a calling class breaks the rebuild and raises a data warning.
    data = json.loads(PREFLOP.read_text())
    data["response"]["hands"] = [h for h in data["response"]["hands"] if h["hand"] != "AA"]
    assert any("probably missing" in w for w in explain(data).warnings)


def test_check_flags_invented_numbers_and_thin_drafts():
    rep = explain(PREFLOP)
    src = load_spot(PREFLOP).data
    thin = "LJ will call or fold 69.4%; instead of that, block, ICM, takeaway. 53.4 0.00 4.3 84.1 43.7"
    assert check_explanation(thin, rep, source=src)["score"] <= 0.5
    good = rep.to_markdown()
    assert check_explanation(good, rep, source=src)["unsupported_numbers"] == []
    assert "72.0%" in check_explanation(good.replace("69.4%", "72.0%"), rep, source=src)["unsupported_numbers"]
