import math

import pytest

from poker_harness.board import board_beaters, classify_combo, composition, showdown_split, texture
from poker_harness.cards import (
    FLUSH,
    STRAIGHT,
    category_of,
    class_combos,
    describe_score,
    evaluate,
    hand_class,
    parse_cards,
)
from poker_harness.icm import allin_call_requirements, bubble_factor, icm_equities, required_equity_from_bubble_factor
from poker_harness.ranges import Range


def ev(s):
    return evaluate(parse_cards(s))


class TestEvaluator:
    def test_ordering(self):
        hands = [
            "2c3d5h7s9c Jd Qh",  # high card
            "2c2d5h7s9c Jd Qh",  # pair
            "2c2d5h5s9c Jd Qh",  # two pair
            "2c2d2h7s9c Jd Qh",  # trips
            "Ac2d3h4s5c Jd Qh",  # wheel
            "2c4c6c8cTc Jd Qh",  # flush
            "2c2d2h7s7c Jd Qh",  # full house
            "2c2d2h2s9c Jd Qh",  # quads
            "9cTcJcQcKc 2d 3h",  # straight flush
        ]
        scores = [ev(h) for h in hands]
        assert scores == sorted(scores)

    def test_wheel_and_broadway(self):
        assert describe_score(ev("Ah2d3c4s5s9c9d")) == "Straight, 5-high"
        assert describe_score(ev("AhKdQcJsTs2c3d")) == "Straight, A-high"
        assert ev("6h2d3c4s5s9c9d") > ev("Ah2d3c4s5s9c9d")

    def test_kickers_and_splits(self):
        assert ev("AhAd Kc 7s 4d 3c 2h") > ev("AhAd Qc 7s 4d 3c 2h")
        board = parse_cards("KsJs6s8sQs")
        assert evaluate(parse_cards("AhAd") + board) == evaluate(parse_cards("2c3d") + board)

    def test_flush_beats_straight(self):
        assert category_of(ev("2c4c6c8cTc9d7h")) == FLUSH
        assert category_of(ev("5d6c7h8s9h2c2d")) == STRAIGHT


class TestRanges:
    def test_parse_counts(self):
        assert Range.parse("22+").total() == 78
        assert Range.parse("A2s+").total() == 48
        assert Range.parse("KTo+").total() == 36
        assert Range.parse("T9s-65s").total() == 20
        assert Range.parse("AK").total() == 16
        assert Range.parse("AsKh:0.22").total() == pytest.approx(0.22)
        assert Range.parse({"QQ": 0.5, "AsKs": 1}).total() == pytest.approx(4.0)

    def test_card_removal(self):
        r = Range.parse("AA")
        assert r.without(parse_cards("As")).total() == 3

    def test_class_helpers(self):
        assert len(class_combos("AKs")) == 4 and len(class_combos("AKo")) == 12 and len(class_combos("TT")) == 6
        assert hand_class(tuple(parse_cards("Ts9s"))) == "T9s"
        assert hand_class(tuple(parse_cards("9sTh"))) == "T9o"


class TestBoard:
    def test_five_flush_board(self):
        b = parse_cards("KsJs6s8sQs")
        bb = board_beaters(b)
        assert sorted(bb.single_card_outs) == sorted(parse_cards("As Ts 9s 7s"))
        t = texture(b)
        assert t.flush_on_board and t.suit_pattern == "five-flush"

    def test_random_hand_has_out_matches_combinatorics(self):
        p = 1 - math.comb(43, 2) / math.comb(47, 2)
        assert p == pytest.approx(0.1647, abs=1e-3)

    def test_classify(self):
        flop = parse_cards("KsJs6h")
        assert classify_combo(parse_cards("As2s"), flop)["draws"] == ["Nut flush draw"]
        assert "Open-ended straight draw" in classify_combo(parse_cards("QdTc"), flop)["draws"]
        assert classify_combo(parse_cards("AhKh"), flop)["label"] == "Top pair"
        assert classify_combo(parse_cards("6c6d"), flop)["label"] == "Set"
        assert classify_combo(parse_cards("AhAd"), flop)["label"] == "Overpair"
        river = parse_cards("KsJs6s8sQs")
        assert classify_combo(parse_cards("2c3d"), river)["label"] == "Plays the board"

    def test_composition_and_showdown(self):
        river = parse_cards("KsJs6s8sQs")
        villain = Range.parse("AsAh, 2c2d, 7s7h")
        comp = composition(villain, river)
        assert comp["Plays the board"]["combos"] == pytest.approx(1)
        split = showdown_split(parse_cards("2h3h"), villain, river)  # plays the board
        assert split["beats_hero"] == 2  # AsAh, 7s7h
        assert split["chops"] == 1  # 2c2d
        split = showdown_split(parse_cards("Ts9h"), villain, river)  # T-high flush
        assert split["beats_hero"] == 1 and split["hero_beats"] == 2


class TestICM:
    def test_textbook_values(self):
        eq = icm_equities([50, 30, 20], [50, 30, 20])
        assert eq == pytest.approx([38.393, 32.75, 28.857], abs=1e-3)
        assert sum(eq) == pytest.approx(100)

    def test_winner_take_all_is_chip_ev(self):
        eq = icm_equities([60, 30, 10], [100])
        assert eq == pytest.approx([60, 30, 10])
        assert bubble_factor([60, 30, 10], [100], 2, 0) == pytest.approx(1.0)

    def test_bubble_factor_short_stack_suffers_more(self):
        stacks, pays = [40, 30, 20, 10], [50, 30, 20]
        assert bubble_factor(stacks, pays, 3, 0) > bubble_factor(stacks, pays, 0, 3) > 1.0

    def test_risk_premium_positive_on_bubble(self):
        m = allin_call_requirements([40, 30, 20, 10], [50, 30, 20], hero=3, villain=0, hero_committed=1, dead_money=1.5)
        assert m.icm_required > m.chip_required
        assert m.risk_premium > 0.05

    def test_required_equity_bf_one_is_pot_odds(self):
        assert required_equity_from_bubble_factor(1.0, 10, 20) == pytest.approx(10 / 30)

    def test_monte_carlo_close_to_exact(self):
        stacks = [30, 25, 20, 15, 10, 9, 8, 7, 6, 5, 4, 3]  # 12 players -> sampled
        pays = [40, 25, 15, 10, 6, 4]
        mc = icm_equities(stacks, pays, samples=60000)
        assert sum(mc) == pytest.approx(sum(pays), rel=1e-6)
        assert mc[0] > mc[5] > mc[-1]
