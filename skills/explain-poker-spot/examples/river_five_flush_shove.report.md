# SB river shove on K♠J♠6♠8♠Q♠ (MTT, ICM)

_Source: GTO Wizard AI solution, MTT General ICM 9-max, 200 players, 50% left. Numbers captured from the Strategy+EV, Breakdown, Equity chart, Summary and Actions tabs on 2026-10-22._

## Judge the decision, not the result

This explanation judges the decision with only the information available when it was made. Which card came next, or who won the pot, doesn't change whether the play was right; if swapping the river card would flip the verdict, we'd be grading the result instead of the decision.

## Set the scene

**Format:** MTT, 9-max, 200 entrants, 50% of the field left, ICM applies.

**Stacks at the start of the hand:** UTG 30.125bb, UTG1 43.125bb, UTG2 35.125bb, LJ 42.125bb (villain), HJ 45.125bb, CO 40.125bb, BTN 90.125bb, SB 25.125bb (hero), BB 100.125bb.

**Action so far:** Preflop: folds to LJ, LJ raises to 2, folds to SB, SB calls, BB folds; Flop [K♠ J♠ 6♠]: SB checks, LJ checks; Turn [8♠]: SB checks, LJ bets 2 (33%), SB calls; River [Q♠]: SB to act.

**Pot:** 10.125bb.

**Behind:** SB 21bb, LJ 38bb, so 21bb effective and a stack-to-pot ratio of 2.1.

LJ covers SB: if they get it all in, SB is the one who can bust. In a tournament that asymmetry matters for ICM (see below).

## Read the board

**Board:** K♠ J♠ 6♠ 8♠ Q♠ (river), five-flush, straight possible, board plays as Flush, K-Q-J-8-6.

All five cards are spades: everyone already has a flush, so the board itself is a Flush, K-Q-J-8-6.

Only 4 specific cards beat the board on their own: A♠ → Flush, A-K-Q-J-8, T♠ → Flush, K-Q-J-T-8, 9♠ → Flush, K-Q-J-9-8, 7♠ → Flush, K-Q-J-8-7. Everything else needs both hole cards to improve, or plays the board.

Combinatorics check: a random two-card hand holds at least one of those 4 cards 16.5% of the time (1 − C(43,2)/C(47,2)), before range effects.

## Shape of both ranges

| Player | Combos | Equity | EQR | EV (bb) |
|---|---|---|---|---|
| SB | 49.9 | 48.6% | 87.0% | – |
| LJ | 100.5 | 51.4% | 104.0% | – |

LJ has the equity lead, 51.4% to 48.6%: a near coin-flip.

LJ's range is 2.0x wider in combos, so it is weighted toward more medium and weak hands.

SB's EQR is 87.0%: it realises less than its raw equity, usually because of position or stack pressure working against it.

**SB by hand category** (Breakdown tab):

| Category | Range % | Combos | Strategy |
|---|---|---|---|
| Straight flush | 2.4% | 1.2 |  |
| Flush (beats the board) | 12.7% | 6.4 |  |
| No made hand (plays the board) | 84.9% | 42.4 |  |

**LJ by hand category** (Breakdown tab):

| Category | Range % | Combos | Strategy |
|---|---|---|---|
| Straight flush | 1.2% | 1.2 |  |
| Flush (beats the board) | 16.3% | 16.4 |  |
| No made hand (plays the board) | 82.5% | 82.9 |  |

Biggest category in each range: SB: No made hand (plays the board) (84.9%); LJ: No made hand (plays the board) (82.5%).

## What the whole range does

Facing this spot, SB's whole range plays: Allin 21 54.5%, Check 45.5%.

In combos: Allin 21 27.2, Check 22.7.

Essentially never used: Bet 2.5. When an option is skipped, ask what it would do worse than the chosen ones.

The range splits fairly evenly between options, so the interesting question is *which* hands go where (see outliers).

SB goes all-in with 54.5% of the range. With a bet that large, check what the shoving hands are: only very strong hands and bluffs (polarised), or also medium hands that can't stand a bet if they check.

## Where the hand sits and its EV

**Hand:** A♠T♠ (Royal flush), which makes: Straight flush.

Solver strategy for this hand: Allin 21 96.9%, Check 3.1%, Bet 2.5 0.0%.

EV by action: Allin 21 27.18bb, Check 27.09bb, Bet 2.5 23.11bb.

The top two actions are within 0.09bb (0.9% of the pot), so the hand is close to indifferent. That is why the solver mixes: choosing either is fine, and the mix matters only to keep the range balanced.

This hand plays Allin 21 96.9% of the time against 54.5% for the range as a whole, so it is an outlier: the explanation has to say what this hand gains from that action that most of the range doesn't.

## Outlier hands and why

The range plays **Allin 21** 54.5% of the time overall. Hands that deviate from that by 30 points or more:
- **Allin 21 more often:** 22 100.0% (Plays the board), 33 100.0% (Plays the board), 44 100.0% (Plays the board), 55 100.0% (Plays the board), 66 100.0% (Plays the board), 54s 100.0% (Plays the board), 65s 100.0% (Plays the board), A♠T♠ 96.9% (Royal flush)
- **Allin 21 less often:** KQs 0.0% (Plays the board), KQo 0.0% (Plays the board), KJo 0.0% (Plays the board)

Average by hand type (unweighted across the rows you captured):

| Hand type | Allin 21 % | Rows |
|---|---|---|
| Royal flush | 96.9% | 1 |
| Plays the board | 70.0% | 10 |

Within Plays the board the strategy still splits sharply. When hands of the same strength act differently, the reason is usually card removal: which opponent hands they block or unblock (see blockers).

## The opponent's response

Facing Allin 21, LJ plays: Call 83.7%, Fold 16.3%.

A 21bb bet into 10.125bb risks 21 to win 10.125: a hand with zero equity needs LJ to fold 67.5% to break even (so the defender's MDF is 32.5%).

LJ folds only 16.3%, far below 67.5%. So the bet can't be profiting as a pure bluff: the hands making it must also win money when called, as value, through equity when called, or by keeping their share of a split pot.

LJ is getting 40.3% pot odds: a call needs at least that much equity in chip EV.

| Hand | Strategy | EV (bb) | Equity | Note |
|---|---|---|---|---|
| A♠A♥ | Call 100.0%, Fold 0.0% | Call 27.83, Fold 0.00 | 96.9% | Nut flush |
| A♥A♦ | Call 100.0%, Fold 0.0% | Call 0.36, Fold 0.00 | 41.3% | Plays the board |
| A♠T♠ | Call 100.0%, Fold 0.0% | Call 29.40, Fold 0.00 | 100.0% | Royal flush |
| 7♠7♥ | Call 100.0%, Fold 0.0% | Call 22.78, Fold 0.00 | 87.0% | 7-high flush |

Near-indifferent hands (EV gap under 0.5bb): A♥A♦. These are the bluff-catchers that set the bettor's ratio of value to bluffs.

Calls that barely clear the price: A♥A♦ (41.3% vs 40.3% needed). Under ICM these are the first calls to become folds.

## What happens on the other line *(includes inference)*

**If SB checks instead:**
- LJ: Allin 21 73.1%, Check 13.6%, Bet 10.1 11.0%, Bet 3.3 2.3%
- SB facing Allin 21: Fold 75.5%, Call 24.5%
So on this line LJ takes the initiative: it shoves 73.1% and SB then folds 75.5%, giving up its share of the pot with every hand that folds. Comparing the lines shows the value of acting first: the player who moves all-in puts the other one to the hard decision.

## How the ranges got here

Every weight in LJ's range is the product of how often each combo took this line on earlier streets. Multiplying the street frequencies shows which street removed which hands:

| Combo | Type | Flop check | Turn bet 2bb | Reaches | Weight seen | Filtered by |
|---|---|---|---|---|---|---|
| A♠T♠ | Royal flush | 60.0% | 82.7% | 50% | 0.50 | – |
| T♠9♠ | Straight flush | 73.8% | 92.4% | 68% | 0.68 | – |
| A♠A♥ | Nut flush | 1.4% | 99.2% | 1% | 0.01 | Flop check |
| A♠K♥ | Nut flush | 28.6% | 77.1% | 22% | 0.22 | Flop check |
| A♠Q♥ | Nut flush | 63.6% | 76.4% | 49% | 0.49 | – |
| A♠J♥ | Nut flush | 85.3% | 55.6% | 47% | 0.47 | Turn bet 2bb |
| A♠T♥ | Nut flush | 7.3% | 99.1% | 7% | 0.07 | Flop check |
| A♠9♥ | Nut flush | 73.5% | 94.7% | 70% | 0.70 | – |
| A♠9♠ | Nut flush | 19.9% | 98.4% | 20% | 0.20 | Flop check |
| A♠7♠ | Nut flush | 75.9% | 96.9% | 74% | 0.74 | – |
| A♠5♠ | Nut flush | 57.4% | 97.7% | 56% | 0.56 | Flop check |
| A♠4♠ | Nut flush | 85.8% | 85.2% | 73% | 0.73 | – |
| A♠3♠ | Nut flush | 70.6% | 89.9% | 63% | 0.63 | – |
| A♠2♠ | Nut flush | 64.7% | 91.8% | 59% | 0.59 | – |
| A♥T♠ | T-high flush | 57.9% | 64.5% | 37% | 0.37 | Flop check |
| T♠T♥ | T-high flush | 65.0% | 98.8% | 64% | 0.64 | – |
| K♥T♠ | T-high flush | 40.1% | 7.8% | 3% | 0.03 | Turn bet 2bb |
| Q♥T♠ | T-high flush | 96.7% | 53.8% | 52% | 0.09 | Turn bet 2bb |
| J♥T♠ | T-high flush | 98.3% | 8.2% | 8% | 0.03 | Turn bet 2bb |
| A♥9♠ | 9-high flush | 51.3% | 44.3% | 23% | 0.23 | Turn bet 2bb |
| 9♠9♥ | 9-high flush | 89.6% | 76.7% | 69% | 0.69 | – |
| 7♠7♥ | 7-high flush | 85.5% | 30.5% | 26% | 0.26 | Turn bet 2bb |

Across these combos, **Flop check** removed the most weight (8.5 of the 22 combos listed). Hands that left the line there show up in a different branch of the tree, not in this river range.

Product and observed weight differ for: Q♥T♠ (52% vs 0.09), J♥T♠ (8% vs 0.03). The usual cause is the preflop step (the hand is only partly in the opening range) if it isn't in the list.

## Blockers and card removal

A♠T♠ removes these LJ combos:

| Group | Combos before | After | Removed |
|---|---|---|---|
| Straight flush | 1.18 | 0.0 | 100.0% |
| Flush | 16.35 | 3.54 | 78.3% |

(The LJ range supplied is partial, so the table only covers the combos you listed.)

A♠T♠ holds A♠, T♠, one of the only cards that beat the board, so LJ can't hold it.

## ICM versus chip EV *(includes inference)*

The solution uses ICM. LJ covers SB, so in an all-in only SB risks busting. Under ICM that makes SB's losses heavier than its wins: SB needs more equity to call off, and LJ can apply pressure with hands that would be too weak in chip EV.

_Add the payout ladder under `format.payouts` to turn this into numbers (bubble factor, risk premium)._

## One-sentence takeaway

**Betting first matters here: after the other line LJ shoves 73.1% and SB folds 75.5%, so hands that check give up the share of the pot they would keep by shoving.**

Also worth remembering:
- LJ folds 16.3%, well short of the 67.5% a zero-equity bluff needs, so every hand that bets has to earn when called too.
- LJ's range here is filtered: Flop check removed most of the hands that would otherwise be at the top of it.

Notes:
- LJ's range above lists only the 17.5 combos that beat the board; the other 82.9 combos play the board.
- SB's per-hand rows are read from the strategy grid colours: cells that looked pure are recorded as 100/0.
- QhTs and JhTs are only partly in LJ's preflop opening range, which is why their observed weight is below the flop x turn product.

## Coverage

13 of 13 framework points covered.
