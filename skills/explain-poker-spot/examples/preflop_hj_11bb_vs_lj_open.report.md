# HJ (11bb) facing LJ's 2bb open (MTT, ICM, 25% left)

_Source: GTO Wizard AI solution, MTT General ICM 9-max, 200 players, 25% of the field left. Captured on 2026-10-22 from the Summary tab of each node (all 1326 combos, averaged into hand classes)._

## Judge the decision, not the result

This explanation judges the decision with only the information available when it was made. Who won the pot, or the board that came, doesn't change whether the play was right; if a different runout would flip the verdict, we'd be grading the result instead of the decision.

## Set the scene

**Format:** MTT, 9-max, 200 entrants, 25% of the field left (about 50 players), ICM applies, average stack 35bb.

**Stacks at the start of the hand:** UTG 35.125bb, UTG1 29.125bb, UTG2 47.125bb, LJ 59.125bb (villain), HJ 11.125bb (hero), CO 53.125bb, BTN 17.125bb, SB 41.125bb, BB 23.125bb.

**Action so far:** Preflop: UTG, UTG1 and UTG2 fold, LJ raises to 2, HJ to act.

**Pot:** 4.63bb.

**Behind:** HJ 11bb, LJ 57bb, so 11bb effective and a stack-to-pot ratio of 2.4.

LJ covers HJ: if they get it all in, HJ is the one who can bust. In a tournament that asymmetry matters for ICM (see below).

**Stack depth:** 11bb effective. Typical of this depth in general (not read from this solution): push/fold depth: most hands either shove or fold, and flatting is rare.

## Shape of both ranges *(partial)*

HJ continues with 13.0% of hands (about 172 combos) and folds the rest.

Range widths: LJ 23.5% of hands (311 combos).

_Partial: No equity chart or breakdown captured, so range strength and categories aren't shown. Capture the Equity chart (equity, EQR, combos) and Breakdown tab for both players._

## What the whole range does

Facing this spot, HJ's whole range plays: Fold 87.0%, Allin 11 12.9%.

Essentially never used: Call. When an option is skipped, ask what it would do worse than the chosen ones.

**The range by action** (each hand listed under the action it plays most; other actions it uses at least 15% of the time in brackets):
- **Allin 11** (12.9%): 44+, A7s+, A5s, A4s (41%), ATo+, KJs+, KQo, QJs
- **Fold** (87.0%): everything else.

## Where the hand sits and its EV

**Hand:** A5s.

Solver strategy for this hand: Allin 11 100.0%, Call 0.0%, Fold 0.0%.

EV by action: Allin 11 0.02bb, Call 0.01bb, Fold 0.00bb.

The top two actions are within 0.01bb (0.2% of the pot), so the hand is close to indifferent. That is why the solver mixes: choosing either is fine, and the mix matters only to keep the range balanced.

This hand plays Allin 11 100.0% of the time against 12.9% for the range as a whole, so it is an outlier: the explanation has to say what this hand gains from that action that most of the range doesn't.

## Borderline hands *(includes inference)*

Inside each hand family, where each action starts and stops. "Above" and "below" are the neighbouring hands just outside the action and what they do instead.

**Allin 11**

| Family | Range | Best | Just above | Worst | Just below | Gaps |
|---|---|---|---|---|---|---|
| Pocket pairs | 44+ | AA | – (top of family) | 44 | 33: Fold 98% |  |
| Suited aces (Axs) | A7s+, A5s | AKs | – (top of family) | A5s | A4s: Fold 59% | A6s: Fold |
| Offsuit aces (Axo) | ATo+ | AKo | – (top of family) | ATo | A9o: Fold |  |
| Suited kings (Kxs) | KJs+ | KQs | – (top of family) | KJs | KTs: Fold |  |
| Offsuit kings (Kxo) | KQo | KQo | – (top of family) | KQo | KJo: Fold |  |
| Suited queens (Qxs) | QJs | QJs | – (top of family) | QJs | QTs: Fold |  |

Split ranges (the action skips a block of hands in the middle): Allin 11 with Suited aces (Axs): A7s+, A5s. A split usually means two reasons for the same action, e.g. value at the top and blockers or fold equity at the bottom (likely, not labelled by the solver).

EVs at the borders: 33 Allin 11 -0.01 vs Fold +0.00bb; A5s Allin 11 +0.02 vs Call +0.01bb; A4s Allin 11 +0.00 vs Call +0.00bb; ATo Allin 11 +0.12 vs Call +0.12bb; A9o Allin 11 -0.07 vs Call +0.00bb; KTs Allin 11 -0.01 vs Call +0.00bb; KJo Allin 11 -0.10 vs Fold +0.00bb. Hands at a border are close to indifferent, so the exact cut-off matters less than the shape.

### Hand-family patterns

Hands that are more aggressive (Allin 11) than stronger hands of the same family:

| Family | Weaker hand | Aggressive % | Stronger hand | Aggressive % |
|---|---|---|---|---|
| Suited aces | A5s | 100.0% | A6s | 0.0% |
| Suited aces | A4s | 40.9% | A6s | 0.0% |

When a weaker hand is more aggressive, the usual reasons are blockers (an ace or king removes the opponent's best continues), playability (the stronger hand prefers to call and see a flop), or the weaker hand being the better bluff because it has less showdown value. The solver doesn't label which; the blockers section shows what each hand removes from the opponent's range.

## The opponent's response

Facing Allin 11 (after CO, BTN, SB and BB fold), LJ plays: Call 53.1%, Fold 46.9%.

Players behind act first: CO folds 96.2% (re-jams or isolates with 99+, AQs+, AKo), BTN folds 94.9% and SB folds 94.9% (both call 99+, AQs+, AQo+), BB folds 94.1% (calls 88+, AJs+, AQo+).

A 11bb bet into 4.63bb risks 11 to win 4.63: a hand with zero equity needs LJ to fold 70.4% to break even (so the defender's MDF is 29.6%).

LJ folds only 46.9%, far below 70.4%. So the bet can't be profiting as a pure bluff: the hands making it must also win money when called, as value, through equity when called, or by keeping their share of a split pot.

LJ is getting 36.5% pot odds: a call needs at least that much equity in chip EV.

| Hand | Strategy | EV (bb) |
|---|---|---|
| 55 | Call 100.0%, Fold 0.0% | 0.19 |
| 66 | Call 100.0%, Fold 0.0% | 0.32 |
| 77 | Call 100.0%, Fold 0.0% | 0.44 |
| 88 | Call 100.0%, Fold 0.0% | 0.58 |
| 99 | Call 100.0%, Fold 0.0% | 0.73 |
| AA | Call 100.0%, Fold 0.0% | 2.46 |
| AKs | Call 100.0%, Fold 0.0% | 1.17 |
| AQs | Call 100.0%, Fold 0.0% | 0.90 |
| AJs | Call 100.0%, Fold 0.0% | 0.61 |
| ATs | Call 100.0%, Fold 0.0% | 0.36 |
| A9s | Call 100.0%, Fold 0.0% | 0.16 |
| A8s | Call 100.0%, Fold 0.0% | 0.09 |
| A7s | Call 100.0%, Fold 0.0% | 0.03 |
| A6s | Fold 100.0%, Call 0.0% | 0.00 |
| A5s | Fold 55.7%, Call 44.3% | 0.00 |
| A4s | Fold 100.0%, Call 0.0% | 0.00 |
| A3s | Fold 100.0%, Call 0.0% | 0.00 |
| A2s | Fold 100.0%, Call 0.0% | 0.00 |
| AKo | Call 100.0%, Fold 0.0% | 1.07 |
| AQo | Call 100.0%, Fold 0.0% | 0.79 |
| AJo | Call 100.0%, Fold 0.0% | 0.48 |
| ATo | Call 100.0%, Fold 0.0% | 0.21 |
| A9o | Fold 100.0%, Call 0.0% | 0.00 |
| A8o | Fold 100.0%, Call 0.0% | 0.00 |

_No equities captured for these rows; add `equity` (EQ % column) to explain which calls are thin._

## Blockers and card removal

Holding A5s removes 15.4% of LJ's calling combos but 10.3% of its folding combos. That moves LJ's fold frequency from 46.9% (no card removal) to 48.4% against this hand.

_Check: rebuilt from the captured rows, LJ folds 46.9%, matching GTO Wizard's 46.9%, so the rows are complete._

Compared with nearby hands:

| Hand | LJ calls removed | Folds removed | LJ folds | Aggressive actions |
|---|---|---|---|---|
| A5s | 15.4% | 10.3% | 48.4% | Allin 11 100.0% |
| A6s | 15.4% | 9.6% | 48.6% | Allin 11 0.0% |
| A4s | 13.6% | 9.1% | 48.2% | Allin 11 40.9% |

The fold frequencies are nearly identical, so card removal alone doesn't explain why these hands differ. The rest of the difference likely comes from how each hand does when called or when it calls instead (equity, playability); capture those nodes to show it.

Overall A5s removes 40.4 of 311.0 combos (13.0%) from LJ's range. Largest classes affected:

| Class | Combos before | After | Removed |
|---|---|---|---|
| AKo | 12.00 | 9.00 | 25.0% |
| AQo | 12.00 | 9.00 | 25.0% |
| AJo | 12.00 | 9.00 | 25.0% |
| ATo | 12.00 | 9.00 | 25.0% |
| A9o | 12.00 | 9.00 | 25.0% |
| A8o | 12.00 | 9.00 | 25.0% |
| A5o | 6.72 | 3.36 | 50.0% |
| 55 | 6.00 | 3.00 | 50.0% |
| AA | 6.00 | 3.00 | 50.0% |
| AKs | 4.00 | 3.00 | 25.0% |

## ICM versus chip EV *(includes inference, partial)*

The solution uses ICM. LJ covers HJ, so in an all-in only HJ risks busting. Under ICM that makes HJ's losses heavier than its wins: HJ needs more equity to call off, and LJ can apply pressure with hands that would be too weak in chip EV.

_Partial: Qualitative only. Add the payout ladder (`format.payouts`) for bubble factors and the risk premium, or capture the same node solved in ChipEV (`icm_compare`)._

## One-sentence takeaway

**At about 11bb facing an open it's jam or fold: jam hands that are happy to be called, because the opener calls about half the time.**

Also worth remembering:
- LJ folds 46.9%, well short of the 70.4% a zero-equity bluff needs, so every hand that bets has to earn when called too.
- A5s blocks LJ's continuing hands (15.4% removed) more than its folds (10.3%), which helps make it a candidate for aggression.

Notes:
- HJ rows list every class HJ jams plus a few notable folds; all other classes fold 100%.
- Per-action EVs (Hands tab hover) captured for A5s, A6s, A4s, KTs, 33, A9o, KJo and ATo; other rows show the Summary EV at the solver mix.
- LJ's range is its full opening range at the response node with GTO Wizard's weights (311 combos).
- Payout ladder not captured, so ICM is qualitative.

## Coverage

Of the 13 framework points: 8 covered, 2 partial, 0 missing, 3 not applicable.

To complete the explanation, capture from GTO Wizard:

- **Shape of both ranges** (partial): No equity chart or breakdown captured, so range strength and categories aren't shown. Capture the Equity chart (equity, EQR, combos) and Breakdown tab for both players.
- **ICM versus chip EV** (partial): Qualitative only. Add the payout ladder (`format.payouts`) for bubble factors and the risk premium, or capture the same node solved in ChipEV (`icm_compare`).
