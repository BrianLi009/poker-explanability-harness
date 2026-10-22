# SB facing LJ's 2bb open, 25bb deep (MTT, ICM)

_Source: GTO Wizard AI solution, MTT General ICM 9-max, 200 players, 50% left. Captured on 2026-10-22 from the Summary tab (all 1326 combos, averaged into hand classes) and the Hands tab._

## Judge the decision, not the result

This explanation judges the decision with only the information available when it was made. Who won the pot, or the board that came, doesn't change whether the play was right; if a different runout would flip the verdict, we'd be grading the result instead of the decision.

## Set the scene

**Format:** MTT, 9-max, 200 entrants, 50% of the field left, ICM applies.

**Stacks at the start of the hand:** UTG 30.125bb, UTG1 43.125bb, UTG2 35.125bb, LJ 42.125bb (villain), HJ 45.125bb, CO 40.125bb, BTN 90.125bb, SB 25.125bb (hero), BB 100.125bb.

**Action so far:** Preflop: folds to LJ, LJ raises to 2, HJ, CO and BTN fold, SB to act.

**Pot:** 4.63bb.

**Behind:** SB 24.5bb, LJ 40bb, so 24.5bb effective and a stack-to-pot ratio of 5.3.

LJ covers SB: if they get it all in, SB is the one who can bust. In a tournament that asymmetry matters for ICM (see below).

**Stack depth:** 24.5bb effective. Typical of this depth in general (not read from this solution): middle depth: min-raise opens, some limps from the SB, and 3-bet/jam vs 3-bet/fold decisions.

## Shape of both ranges *(partial)*

SB continues with 21.6% of hands (about 286 combos) and folds the rest.

Range widths: LJ 22.2% of hands (294 combos).

_Partial: No equity chart or breakdown captured, so range strength and categories aren't shown. Capture the Equity chart (equity, EQR, combos) and Breakdown tab for both players._

## What the whole range does

Facing this spot, SB's whole range plays: Fold 78.4%, Call 10.9%, Raise 6 6.4%, Allin 25 4.3%.

**The range by action** (each hand listed under the action it plays most; other actions it uses at least 15% of the time in brackets):
- **Call** (10.9%): 77-22, AJs-A7s, A5s, A6s (46%), A4s (44%), A3s (21%), AJo, ATo (32%), KQs, K9s-K7s, KJo+, QTs-Q9s, QJs (47%), Q8s (17%), QJo (37%), J9s+, T8s+, 98s, 87s, 76s (44%), 65s, 54s
- **Raise 6** (6.4%): JJ+, 88 (49%), AQs+, A6s, A2s, AJs (48%), A3s (18%), ATo, AKo (46%), AJo (30%), A9o (45%), K7s (26%), KQo (36%), Q8s, Q9s (19%), QJo
- **Allin 25** (4.3%): TT-88, 55 (29%), 44 (26%), A4s-A3s, AQo+, AJo (29%), KJs-KTs, QJs, QTs (26%), JTs (19%)
- **Fold** (78.4%): everything else.

## Where the hand sits and its EV

**Hand:** A4s.

Solver strategy for this hand: Allin 25 53.4%, Call 43.6%, Raise 6 3.0%, Fold 0.0%.

EV by action: Allin 25 0.05bb, Raise 6 0.05bb, Call 0.05bb, Fold 0.00bb.

The top two actions are within 0.00bb (0.0% of the pot), so the hand is close to indifferent. That is why the solver mixes: choosing either is fine, and the mix matters only to keep the range balanced.

This hand plays Allin 25 53.4% of the time against 4.3% for the range as a whole, so it is an outlier: the explanation has to say what this hand gains from that action that most of the range doesn't.

## Borderline hands *(includes inference)*

Inside each hand family, where each action starts and stops. "Above" and "below" are the neighbouring hands just outside the action and what they do instead.

**Call**

| Family | Range | Best | Just above | Worst | Just below | Gaps |
|---|---|---|---|---|---|---|
| Pocket pairs | 77-22 | 77 | 88: Allin 25 50% | 22 | – (bottom of family) |  |
| Suited aces (Axs) | AJs-A7s, A5s | AJs | AQs: Raise 6 | A5s | A4s: Allin 25 53% | A6s: Raise 6 54% |
| Offsuit aces (Axo) | AJo | AJo | AQo: Allin 25 | AJo | ATo: Raise 6 68% |  |
| Suited kings (Kxs) | KQs, K9s-K7s | KQs | – (top of family) | K7s | K6s: Fold 94% | KJs: Allin 25 99%, KTs: Allin 25 |
| Offsuit kings (Kxo) | KJo+ | KQo | – (top of family) | KJo | KTo: Fold 99% |  |
| Suited queens (Qxs) | QTs-Q9s | QTs | QJs: Allin 25 53% | Q9s | Q8s: Raise 6 72% |  |
| Suited jacks (Jxs) | J9s+ | JTs | – (top of family) | J9s | J8s: Fold 99% |  |
| Suited tens (Txs) | T8s+ | T9s | – (top of family) | T8s | T7s: Fold |  |
| Suited nines (9xs) | 98s | 98s | – (top of family) | 98s | 97s: Fold 99% |  |
| Suited eights (8xs) | 87s | 87s | – (top of family) | 87s | 86s: Fold |  |
| Suited sixes (6xs) | 65s | 65s | – (top of family) | 65s | 64s: Fold |  |
| Suited fives (5xs) | 54s | 54s | – (top of family) | 54s | 53s: Fold |  |

**Raise 6**

| Family | Range | Best | Just above | Worst | Just below | Gaps |
|---|---|---|---|---|---|---|
| Pocket pairs | JJ+ | AA | – (top of family) | JJ | TT: Allin 25 98% |  |
| Suited aces (Axs) | AQs+, A6s, A2s | AKs | – (top of family) | A2s | – (bottom of family) | AJs: Call 52%, ATs: Call, A9s: Call and 5 more |
| Offsuit aces (Axo) | ATo | ATo | AJo: Call 41% | ATo | A9o: Fold 55% |  |
| Suited queens (Qxs) | Q8s | Q8s | Q9s: Call 81% | Q8s | Q7s: Fold |  |
| Offsuit queens (Qxo) | QJo | QJo | – (top of family) | QJo | QTo: Fold |  |

**Allin 25**

| Family | Range | Best | Just above | Worst | Just below | Gaps |
|---|---|---|---|---|---|---|
| Pocket pairs | TT-88 | TT | JJ: Raise 6 | 88 | 77: Call 96% |  |
| Suited aces (Axs) | A4s-A3s | A4s | A5s: Call 92% | A3s | A2s: Raise 6 86% |  |
| Offsuit aces (Axo) | AQo+ | AKo | – (top of family) | AQo | AJo: Call 41% |  |
| Suited kings (Kxs) | KJs-KTs | KJs | KQs: Call | KTs | K9s: Call |  |
| Suited queens (Qxs) | QJs | QJs | – (top of family) | QJs | QTs: Call 74% |  |

Split ranges (the action skips a block of hands in the middle): Call with Suited aces (Axs): AJs-A7s, A5s; Call with Suited kings (Kxs): KQs, K9s-K7s; Raise 6 with Suited aces (Axs): AQs+, A6s, A2s. A split usually means two reasons for the same action, e.g. value at the top and blockers or fold equity at the bottom (likely, not labelled by the solver).

_Capture per-action EVs (Hands tab hover) for the worst hand in and the best hand out of each action to show how close the border is._

### Hand-family patterns

Hands that are more aggressive (Allin 25 + Raise 6) than stronger hands of the same family:

| Family | Weaker hand | Aggressive % | Stronger hand | Aggressive % |
|---|---|---|---|---|
| Suited aces | A6s | 54.2% | A7s | 5.2% |
| Suited aces | A4s | 56.4% | A5s | 7.9% |
| Suited aces | A3s | 78.7% | A5s | 7.9% |
| Suited aces | A2s | 87.5% | A4s | 56.4% |
| Suited kings | KJs | 98.8% | KQs | 0.0% |
| Suited kings | KTs | 99.9% | KQs | 0.0% |

When a weaker hand is more aggressive, the usual reasons are blockers (an ace or king removes the opponent's best continues), playability (the stronger hand prefers to call and see a flop), or the weaker hand being the better bluff because it has less showdown value. The solver doesn't label which; the blockers section shows what each hand removes from the opponent's range.

How the aggressive hands split between the all-in (Allin 25) and the smaller raise (Raise 6):

| Family | Hand | Allin 25 | Raise 6 | Prefers |
|---|---|---|---|---|
| Pocket pairs | AA | 0.0% | 100.0% | Raise 6 |
| Pocket pairs | KK | 0.0% | 100.0% | Raise 6 |
| Pocket pairs | QQ | 0.0% | 100.0% | Raise 6 |
| Pocket pairs | JJ | 0.0% | 100.0% | Raise 6 |
| Pocket pairs | TT | 97.6% | 2.4% | Allin 25 |
| Pocket pairs | 99 | 85.3% | 14.7% | Allin 25 |
| Pocket pairs | 88 | 50.3% | 49.4% | Allin 25 |
| Suited aces | AKs | 0.0% | 100.0% | Raise 6 |
| Suited aces | AQs | 0.0% | 100.0% | Raise 6 |
| Suited aces | A6s | 0.0% | 54.2% | Raise 6 |
| Suited aces | A4s | 53.4% | 3.0% | Allin 25 |
| Suited aces | A3s | 60.2% | 18.5% | Allin 25 |
| Suited aces | A2s | 1.9% | 85.6% | Raise 6 |
| Offsuit aces | AKo | 54.4% | 45.6% | Allin 25 |
| Offsuit aces | AQo | 100.0% | 0.0% | Allin 25 |
| Offsuit aces | AJo | 29.1% | 29.9% | Raise 6 |

The small raise goes to AA, KK, QQ, JJ, AKs, AQs; the all-in goes to TT, 99, 88, A4s, A3s, AKo. Typically the strongest hands raise small because they want to be called or face a re-raise, while hands that play badly after the flop or need fold equity prefer to get it in now.

## The opponent's response

Facing Allin 25 (after BB folds), LJ plays: Fold 69.4%, Call 30.6%.

BB acts first and folds 94.9%, calling only 99+, AQs+, AKo and AQo.

A 24.5bb bet into 4.63bb risks 24.5 to win 4.63: a hand with zero equity needs LJ to fold 84.1% to break even (so the defender's MDF is 15.9%).

LJ folds only 69.4%, far below 84.1%. So the bet can't be profiting as a pure bluff: the hands making it must also win money when called, as value, through equity when called, or by keeping their share of a split pot.

LJ is getting 44.1% pot odds: a call needs at least that much equity in chip EV.

| Hand | Strategy | EV (bb) |
|---|---|---|
| 44 | Fold 100.0%, Call 0.0% | 0.00 |
| 55 | Fold 100.0%, Call 0.0% | 0.00 |
| 66 | Fold 99.1%, Call 0.9% | 0.00 |
| 77 | Fold 66.2%, Call 33.8% | 0.00 |
| 88 | Call 100.0%, Fold 0.0% | 0.20 |
| 99 | Call 100.0%, Fold 0.0% | 0.74 |
| AA | Call 100.0%, Fold 0.0% | 4.31 |
| AKs | Call 100.0%, Fold 0.0% | 1.86 |
| AQs | Call 100.0%, Fold 0.0% | 0.94 |
| AJs | Call 100.0%, Fold 0.0% | 0.29 |
| ATs | Call 72.9%, Fold 27.1% | 0.01 |
| A9s | Fold 100.0%, Call 0.0% | 0.00 |
| A5s | Fold 100.0%, Call 0.0% | 0.00 |
| A4s | Fold 100.0%, Call 0.0% | 0.00 |
| AKo | Call 100.0%, Fold 0.0% | 1.66 |
| AQo | Call 100.0%, Fold 0.0% | 0.68 |
| AJo | Fold 67.2%, Call 32.8% | 0.00 |
| ATo | Fold 100.0%, Call 0.0% | 0.00 |
| KK | Call 100.0%, Fold 0.0% | 3.22 |
| KQs | Call 74.2%, Fold 25.8% | 0.00 |
| KJs | Fold 99.3%, Call 0.7% | 0.00 |
| KQo | Fold 100.0%, Call 0.0% | 0.00 |
| QQ | Call 100.0%, Fold 0.0% | 2.74 |
| JJ | Call 100.0%, Fold 0.0% | 2.27 |

_No equities captured for these rows; add `equity` (EQ % column) to explain which calls are thin._

## What happens on the other line *(partial)*

**If SB 3-bets small to 6bb instead (BB folds):**
- LJ facing Raise 6: Fold 43.7%, Call 33.1%, Allin 25 23.0%, Raise 12 0.2%
Against the small 3-bet LJ folds only 43.7% (vs 69.4% against the jam) and 4-bet jams 23.0%, including A4s 78.4% and A5s 39.4%. A hand like A4s that 3-bets small would face that jam and have to fold its equity away; jamming first takes LJ's 4-bet option off the table.
LJ folds 69.4% to the main line but 43.7% here, so the main line gets LJ to fold far more often. Both numbers are conditional on the action reaching that node (e.g. other players folding first).

_Partial: No line captured after Call. Any reason given for not choosing it is inference; capture the node after it to explain it from the data._

## Blockers and card removal

Holding A4s removes 15.2% of LJ's calling combos but 8.9% of its folding combos. That moves LJ's fold frequency from 69.4% (no card removal) to 70.9% against this hand.

_Check: rebuilt from the captured rows, LJ folds 69.4%, matching GTO Wizard's 69.4%, so the rows are complete._

Compared with nearby hands:

| Hand | LJ calls removed | Folds removed | LJ folds | Aggressive actions |
|---|---|---|---|---|
| A4s | 15.2% | 8.9% | 70.9% | Allin 25 53.4%, Raise 6 3.0% |
| A5s | 15.2% | 9.7% | 70.8% | Allin 25 7.9%, Raise 6 0.0% |
| A3s | 15.2% | 8.0% | 71.1% | Allin 25 60.2%, Raise 6 18.5% |

The fold frequencies are nearly identical, so card removal alone doesn't explain why these hands differ. The rest of the difference likely comes from how each hand does when called or when it calls instead (equity, playability); capture those nodes to show it.

Overall A4s removes 31.9 of 294.0 combos (10.8%) from LJ's range. Largest classes affected:

| Class | Combos before | After | Removed |
|---|---|---|---|
| AKo | 12.00 | 9.00 | 25.0% |
| AQo | 12.00 | 9.00 | 25.0% |
| AJo | 12.00 | 9.00 | 25.0% |
| ATo | 12.00 | 9.00 | 25.0% |
| A9o | 12.00 | 9.00 | 25.0% |
| AA | 6.00 | 3.00 | 50.0% |
| AKs | 4.00 | 3.00 | 25.0% |
| AQs | 4.00 | 3.00 | 25.0% |
| AJs | 4.00 | 3.00 | 25.0% |
| ATs | 4.00 | 3.00 | 25.0% |

## ICM versus chip EV *(includes inference, partial)*

The solution uses ICM. LJ covers SB, so in an all-in only SB risks busting. Under ICM that makes SB's losses heavier than its wins: SB needs more equity to call off, and LJ can apply pressure with hands that would be too weak in chip EV.

_Partial: Qualitative only. Add the payout ladder (`format.payouts`) for bubble factors and the risk premium, or capture the same node solved in ChipEV (`icm_compare`)._

## One-sentence takeaway

**LJ folds 69.4% to Allin 25 but only 43.7% to Raise 6, and re-raises 23.2% against it (Allin 25 23.0% + Raise 12 0.2%): choosing between the two is mostly about how often you win the pot without a fight.**

Also worth remembering:
- LJ folds 69.4%, well short of the 84.1% a zero-equity bluff needs, so every hand that bets has to earn when called too.
- A4s blocks LJ's continuing hands (15.2% removed) more than its folds (8.9%), which helps make it a candidate for aggression.

Notes:
- Hand rows list every class SB plays; all other classes fold 100%.
- Class strategies are the combo-weighted average of GTO Wizard's Summary rows; EV is the hand's EV at its best mix (Summary 'EV' column).
- LJ's range is its full opening range with GTO Wizard's weights.
- The response node is LJ facing the shove after BB folds; BB folds 94.9% first.

## Coverage

Of the 13 framework points: 8 covered, 3 partial, 0 missing, 2 not applicable.

To complete the explanation, capture from GTO Wizard:

- **Shape of both ranges** (partial): No equity chart or breakdown captured, so range strength and categories aren't shown. Capture the Equity chart (equity, EQR, combos) and Breakdown tab for both players.
- **What happens on the other line** (partial): No line captured after Call. Any reason given for not choosing it is inference; capture the node after it to explain it from the data.
- **ICM versus chip EV** (partial): Qualitative only. Add the payout ladder (`format.payouts`) for bubble factors and the risk premium, or capture the same node solved in ChipEV (`icm_compare`).
