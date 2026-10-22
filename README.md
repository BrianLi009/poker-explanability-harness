# Poker explainability harness

A Claude plugin and skill that explains tournament poker spots the way a good coach would, using the numbers you already see in GTO Wizard.

GTO Wizard tells you **what** the strategy is. This harness turns those numbers into **why**: it organises them into a 13-point coaching framework, does the small amount of arithmetic GTO Wizard doesn't show (ICM bubble factors and risk premium, break-even fold frequencies, card removal, which cards beat the board, street-by-street range filtering) and tells you which data is still missing for a complete explanation.

It does **not** solve the game. Every frequency, EV and range comes from GTO Wizard.

```
GTO Wizard node ──capture──▶ spot.json ──harness──▶ report.md / report.json / LLM brief
```

## Install

The repo is a Claude plugin (`poker-explainer`) containing one skill (`explain-poker-spot`). The skill bundles the harness code, so it needs nothing but Python 3.10+.

**Claude Code**

```
/plugin install poker-explainer --marketplace BrianLi009/poker-explanability-harness
```

On older Claude Code versions, add the marketplace first: `/plugin marketplace add BrianLi009/poker-explanability-harness`, then `/plugin install poker-explainer@poker-explainability`.

**Claude app** (desktop or web, with plugins): run `tools/build.sh` and open `dist/poker-explainer.plugin` in Claude, or attach it to a chat and accept it.

**Skill only** (claude.ai): run `tools/build.sh` and upload `dist/explain-poker-spot.zip` in Claude's Skills settings.

**Plain Python**, without Claude:

```bash
pip install .                 # installs the poker-harness command
poker-harness explain skills/explain-poker-spot/examples/river_five_flush_shove.json
```

## Using it with Claude

Open a spot in GTO Wizard and ask Claude something like "why does SB shove here?" or "explain this spot like a coach". With the skill installed, Claude:

1. reads the spot (from your GTO Wizard tab via Claude in Chrome, from screenshots, or from numbers you paste), prioritising the node, your hand and the opponent's response,
2. writes a spot file and runs the harness, which checks the data and computes ICM pressure, break-even folds, card removal and range filtering,
3. writes the explanation from those facts, marking anything inferred, and scores its own draft for skipped framework points before answering.

Quick numeric questions work too: "what's the bubble factor for the 10bb stack against the chip leader with 40/30/20/10 stacks and 50/30/20 payouts?"

## Command line

Run from the skill folder with no install (`python3 skills/explain-poker-spot/scripts/harness.py ...`) or with `poker-harness ...` after `pip install .`:

```bash
harness.py explain spot.json [--format md|json|brief] [-o OUT]   # report, facts, or LLM brief
harness.py dashboard spot.json -o dashboard.html                 # visual page for the spot
harness.py validate spot.json                                    # data problems
harness.py check spot.json draft.md                              # score a written explanation
harness.py board KsJs6s8sQs                                      # texture + what beats the board
harness.py icm --stacks 40 30 20 10 --payouts 50 30 20 --hero 3 --villain 0
```

The **Coverage** section at the end of every report lists the framework points the data couldn't support and which GTO Wizard tab has them. See [capture-guide](skills/explain-poker-spot/references/capture-guide.md) for the tab-by-tab mapping and [spot-schema](skills/explain-poker-spot/references/spot-schema.md) for the file format. `scripts/gtowizard_summary.js` reads every combo from GTO Wizard's Summary tab.

## Repo layout

```
.claude-plugin/plugin.json        plugin manifest (+ marketplace.json, icon.png)
skills/explain-poker-spot/
  SKILL.md                        the workflow Claude follows
  scripts/harness.py              no-install CLI entry point
  scripts/poker_harness/          the Python package
  scripts/gtowizard_summary.js    Summary-tab capture
  references/                     framework, spot schema, capture guide
  examples/                       two captured spots + rendered reports
tests/                            pytest suite
tools/build.sh                    builds dist/*.plugin and the skill .zip
```

## The framework

Distilled from how GTO Wizard's hand analyses, ICMIZER's review guide, Kevin Rabichow, Carrot Corner, Octopi and Barry Carter break hands down (details in [framework](skills/explain-poker-spot/references/framework.md)):

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
| `poker_harness.preflop` | Global range shape by action and family, borderline hands per action (best/worst in, what the neighbours do, EVs at the border), stack-depth regime, continuing-range outliers per action, hand-family patterns (e.g. A4s jams while A5s calls, KJs jams while KQs calls), jam vs small 3-bet sizing split, card removal split by how the opponent responds. |
| `poker_harness.postflop` | Board texture and single-card outs, plays-the-board share, hand-type labels for grid rows, break-even fold frequency for bets, line rewind. |
| `poker_harness.icm` | Malmuth-Harville ICM (exact up to 11 players, sampled above), bubble factor, risk premium, ICM break-even equity for all-in calls, field padding for big MTTs. |
| `poker_harness.board`, `ranges`, `cards` | Combo counting, range parsing (`22+, A2s+, T9s-65s, AsKh:0.22`), hand evaluation for classification. |
| `poker_harness.brief` | Packs the facts and framework into an LLM prompt, and scores a written explanation for skipped points and missing key numbers. |

## Worked examples

The examples in `skills/explain-poker-spot/examples/` were captured from a real GTO Wizard solution (MTT, ICM, 9-max, 200 entrants, 50% left):

* **`river_five_flush_shove.json`**: SB shoves 21bb on K♠J♠6♠8♠Q♠. The report shows only four cards beat the board, that LJ folds 16.3% when a zero-equity shove needs 67.5%, that on the check line LJ shoves 73.1% and SB folds 75.5%, and that LJ's flop check filtered out most of its nut flushes. Takeaway: hands that check give up the share of the pot they'd keep by shoving.
* **`preflop_hj_11bb_vs_lj_open.json`**: HJ with 11bb facing the same kind of open. Global shape: jam 12.9% (44+, A7s+, A5s, ATo+, KJs+, KQo, QJs), fold the rest. Borderlines: the jam stops at 44 (33 folds), A5s jams while A6s folds, and the border EVs are within ±0.02bb.
* **`preflop_sb_vs_lj_open.json`**: SB at 25bb facing LJ's 2bb open, with A4s. The report separates the small 3-bet hands (AA–JJ, AKs, AQs) from the jams (TT–88, AQo, KJs, A4s), shows LJ folds 69.4% to the jam but only 43.7% to a small 3-bet (and 4-bet jams 23%), and that A4s removes 15.2% of LJ's calls versus 8.9% of its folds. The card-removal arithmetic reproduces GTO Wizard's 69.4% fold frequency from the captured rows.

## Testing

```bash
pip install pytest && python -m pytest
claude plugin validate .   # plugin structure
```

## Limits

* The harness can only explain what you capture. A missing response node is the most common reason an explanation is wrong.
* ICM numbers need a payout ladder; for big fields the off-table players are modelled as average stacks, so treat them as directional rather than matching GTO Wizard exactly.
* Hand-family and blocker sections suggest reasons (blockers, playability, fold equity) and are flagged as inference; the solver doesn't label its reasons.
* The capture script reads GTO Wizard's page as rendered in October 2026 and may need its selectors updated if the site changes.
