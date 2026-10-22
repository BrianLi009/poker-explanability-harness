# The explanation framework

Every report follows the same checklist. It's distilled from how strong coaches and solver sites break hands down:

* **GTO Wizard's hand analyses** walk a hand street by street, give a verdict at each decision and back it with tool evidence (Breakdown tab to filter a bet range, Blockers tab, rewinding to an earlier street to see which bluffs reach the river).
* **ICMIZER / Postflopizer's review guide** orders the questions: range shapes, what the range does, outlier hands, the bluffs that go with the value, good and bad runouts, and EV of the key hands.
* **Kevin Rabichow** frames the question the player has to answer and stresses not reading results as progress and not using tools you don't understand.
* **Carrot Corner (Peter Clarke)** reasons out loud with hand reading and opponent types, and has readers decide before seeing the answer.
* **Octopi's Vault** pairs solver analysis with real footage of the hand.
* **Barry Carter** recommends solving the same ICM spot in ChipEV to isolate what ICM changes.

| # | Point | What a good explanation says |
|---|---|---|
| 1 | Judge the decision, not the result | Whether the play was right doesn't depend on the runout. |
| 2 | Set the scene | Format, stacks, positions, pot, effective stack, who covers whom. |
| 3 | Read the board | Texture and what actually beats the board. |
| 4 | Shape of both ranges | Equity, EQR, combos and categories for both players. |
| 5 | What the whole range does | Action frequencies before any single hand. |
| 6 | Where the hand sits and its EV | The hand's strategy, EV gap, and whether it's pure or mixed. |
| 7 | Outlier hands and why | Hands that deviate from the range and the pattern behind them. |
| 8 | The opponent's response | How the opponent reacts, and what that says about why the action works. |
| 9 | What happens on the other line | The node after the alternative action. |
| 10 | How the ranges got here | Earlier-street frequencies that shaped the current range. |
| 11 | Blockers and card removal | What the hand removes from the opponent's range, split by how those hands respond. |
| 12 | ICM versus chip EV | Bubble factor, risk premium, who is under pressure. |
| 13 | One-sentence takeaway | A plain-English rule the player can reuse. |

## What the harness computes, and what it doesn't

The harness never solves. It only:

* counts and classifies combos (board texture, which cards beat the board, hand categories, card removal),
* does break-even arithmetic (pot odds, the fold frequency a zero-equity bet needs, MDF),
* computes ICM quantities GTO Wizard doesn't display (bubble factor, risk premium, ICM break-even equity),
* multiplies street frequencies for the rewind.

Everything strategic (frequencies, EVs, ranges, equities) comes from GTO Wizard. Sections that reason beyond the numbers are flagged *(includes inference)*.
