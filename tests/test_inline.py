import json
import re
from pathlib import Path

from poker_harness import explain, load_spot
from poker_harness.cli import main
from poker_harness.inline import action_colors, inline_data, render_inline

EX = Path(__file__).resolve().parent.parent / "skills" / "explain-poker-spot" / "examples"
HJ = EX / "preflop_hj_11bb_vs_lj_open.json"
SB = EX / "preflop_sb_vs_lj_open.json"
RIVER = EX / "river_five_flush_shove.json"


def _payload(frag: str) -> dict:
    return json.loads(re.search(r"const PH=(\{.*?\});\n", frag, re.S).group(1))


def test_inline_is_a_chat_fragment():
    spot = load_spot(HJ)
    frag = render_inline(spot, explain(spot))
    assert not re.search(r"<!doctype|<html|<head|<body", frag, re.I)
    assert frag.startswith('<h2 class="sr-only">')
    assert "http" not in frag  # no external requests
    assert "<!--" not in frag and "/*" not in frag
    assert len(frag) < 40_000


def test_preflop_grid_is_complete_and_hero_selected():
    spot = load_spot(HJ)
    d = inline_data(spot, explain(spot))
    assert len(d["rows"]) == 169
    assert d["hero_hand"] == "A5s"
    assert d["rows"]["A5s"]["ev"] is not None
    assert d["breakeven"] is not None


def test_response_bar_puts_fold_first():
    spot = load_spot(SB)
    d = inline_data(spot, explain(spot))
    assert d["response"]["parts"][0][0] == "fold"
    for alt in d["alternatives"]:
        assert alt["label"]
        assert alt["parts"][0][0] == "fold"


def test_postflop_uses_rows_not_grid():
    spot = load_spot(RIVER)
    d = inline_data(spot, explain(spot))
    assert d["preflop"] is False
    assert all(" " not in a["name"] or a["pct"] >= 0 for a in d["actions"])
    assert all(alt["label"] and "null" not in alt["label"] for alt in d["alternatives"])
    assert all(t for t in d["tiles"])


def test_action_colors():
    c = action_colors(["Allin 23", "Raise 7", "Raise 12", "Call", "Fold"])
    assert c["Allin 23"] != c["Raise 7"] != c["Raise 12"]
    assert c["Call"] == action_colors(["Check"])["Check"]


def test_cli_inline(tmp_path, capsys):
    out = tmp_path / "v.html"
    assert main(["inline", str(HJ), "-o", str(out)]) == 0
    assert _payload(out.read_text())["hero_hand"] == "A5s"
