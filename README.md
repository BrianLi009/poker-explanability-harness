# Poker explainability harness

Explain tournament poker spots the way a good coach would, using the numbers you already see in GTO Wizard.

GTO Wizard tells you **what** the strategy is. This harness turns those numbers into **why**: it organises them into a 13-point coaching framework, does the small amount of arithmetic GTO Wizard doesn't show (ICM bubble factors and risk premium, break-even fold frequencies, card removal, which cards beat the board, street-by-street range filtering) and tells you which data is still missing for a complete explanation.

It does **not** solve the game. Every frequency, EV and range comes from GTO Wizard.

```
GTO Wizard node ──capture──▶ spot.json ──harness──▶ report.md / report.json / LLM brief
```

## Quick start

```bash
pip install -e .            # or just run from the repo; no dependencies
python -m poker_harness explain examples/river_five_flush_shove.json
python -m poker_harness explain examples/preflop_sb_vs_lj_open.json
```

Other commands:

```bash
python -m poker_harness board KsJs6s8sQs           # texture + what beats the board
python -m poker_harness icm --stacks 40 30 20 10 --payouts 50 30 20 --hero 3 --villain 0
python -m poker_harness explain spot.json --format brief   # prompt + facts for an LLM
python -m poker_harness check spot.json my_explanation.md  # score a written explanation
python -m poker_harness validate spot.json
```

## How it's meant to be used

Next to GTO Wizard. Open the spot, capture the nodes you care about into a spot file (by hand, with `capture/gtowizard_summary.js`, or by asking Claude in Chrome to read the tabs), run the harness, and read the report. The **Coverage** section at the end of every report lists the framework points the data couldn't support and exactly which GTO Wizard tab to grab them from.

See [docs/capture-guide.md](docs/capture-guide.md) for the tab-by-tab mapping and [docs/spot-schema.md](docs/spot-schema.md) for the file format.

## The framework

Distilled from how GTO Wizard's hand analyses, ICMIZER's review guide, Kevin Rabichow, Carrot Corner, Octopi and Barry Carter break hands down (details in [docs/framework.md](docs/framework.md)):

1. Judge the decision, not the result
2. Set the scene (stacks, positions, who covers whom)
3. Read the board (texture, what beats the board)
4. Shape of both ranges (equity, EQR, categories)
5. What the whole range does
6. Where the hand sits and its EV (pure vs mixed)
7. Outlier hands and why
8. The opponent's response
9. What happens on the other line
10. How the ranges got here (rewind earlier streets)
11. Blockers and card removal
12. ICM versus chip EV
13. One-sentence takeaway

## Modules

| Module | What it adds |
|---|---|
| `poker_harness.preflop` | Stack-depth regime, continuing-range outliers per action, hand-family patterns (e.g. A4s jams while A5s calls, KJs jams while KQs calls), jam vs small 3-bet sizing split, card removal split by how the opponent responds. |
| `poker_harness.postflop` | Board texture and single-card outs, plays-the-board share, hand-type labels for grid rows, break-even fold frequency for bets, line rewind. |
| `poker_harness.icm` | Malmuth-Harville ICM (exact up to 11 players, sampled above), bubble factor, risk premium, ICM break-even equity for all-in calls, field padding for big MTTs. |
| `poker_harness.board`, `ranges`, `cards` | Combo counting, range parsing (`22+, A2s+, T9s-65s, AsKh:0.22`), hand evaluation for classification. |
| `poker_harness.brief` | Packs the facts and framework into an LLM prompt, and scores a written explanation for skipped points and missing key numbers. |

## Worked examples

Both examples were captured from a real GTO Wizard solution (MTT, ICM, 9-max, 200 entrants, 50% left):

* **`examples/river_five_flush_shove.json`**: SB shoves 21bb on K♠J♠6♠8♠Q♠. The report shows only four cards beat the board, that LJ folds 16.3% when a zero-equity shove needs 67.5%, that on the check line LJ shoves 73.1% and SB folds 75.5%, and that LJ's flop check filtered out most of its nut flushes. Takeaway: hands that check give up the share of the pot they'd keep by shoving.
* **`examples/preflop_sb_vs_lj_open.json`**: SB at 25bb facing LJ's 2bb open, with A4s. The report separates the small 3-bet hands (AA–JJ, AKs, AQs) from the jams (TT–88, AQo, KJs, A4s), shows LJ folds 69.4% to the jam but only 43.7% to a small 3-bet (and 4-bet jams 23%), and that A4s removes 15.2% of LJ's calls versus 8.9% of its folds. The card-removal arithmetic reproduces GTO Wizard's 69.4% fold frequency from the captured rows.

## Testing

```bash
pip install pytest && python -m pytest
```

## Limits

* The harness can only explain what you capture. A missing response node is the most common reason an explanation is wrong.
* ICM numbers need a payout ladder; for big fields the off-table players are modelled as average stacks, so treat them as directional rather than matching GTO Wizard exactly.
* Hand-family and blocker sections suggest reasons (blockers, playability, fold equity) and are flagged as inference; the solver doesn't label its reasons.
* The capture script reads GTO Wizard's page as rendered in October 2026 and may need its selectors updated if the site changes.
