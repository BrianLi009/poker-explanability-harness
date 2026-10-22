# Capturing a spot from GTO Wizard

The harness explains; GTO Wizard solves. This guide maps each framework point to the GTO Wizard tab that holds the numbers. You don't need everything: start with the node and the opponent's response, then add blocks until the Coverage section is clean.

| Framework point | Where it lives in GTO Wizard | Spot field |
|---|---|---|
| Set the scene | Header bar (stacks), URL (`stacks=`, `preflop_actions=`), node pot | `table`, `history`, `pot`, `stacks_behind` |
| Read the board | Board cards | `board` |
| Shape of both ranges | **Equity chart** tab (equity, EQR, combos per player) and **Breakdown** tab (categories) | `equity`, `breakdown` |
| What the whole range does | **Overview** → action boxes (frequency and combos) | `node.actions`, `node.combos` |
| Where the hand sits and its EV | **Hands** tab, hover the hand (EV per action); **Summary** tab row | `hero_hand` |
| Outlier hands | **Summary** tab with no cell selected lists every combo; or read the grid | `hands` |
| The opponent's response | Click the action in the header bar to move to the next node; read its Overview, pot odds and Summary | `response`, `bet` |
| The other line | Pick each other action the hero's range uses (e.g. Check, or Call and the small 3-bet) in the header and follow it one or two nodes | `alternatives` (one entry per action) |
| How the ranges got here | Go back to each earlier node, select the combo and read its frequency for the action actually taken | `rewind` |
| Blockers | **Blockers** tab (value/trash removal) or the opponent's Summary rows with weights | `blockers_tab`, `ranges` |
| ICM vs chip EV | Solution settings (ICM / ChipEV), payout structure | `icm_compare`, `format.payouts` |

## Faster capture with the Summary script

`scripts/gtowizard_summary.js` reads the Summary tab for the node you're on (all combos, scrolling the virtual table for you) and returns JSON with:

* `node.actions`: the range-weighted action frequencies,
* `hands`: one row per hand class (combo-weighted strategy, EV, weight),
* `columns` / `ev_column`: which columns the table had (EV in chip-EV solutions, CSTE in ICM solutions),
* `combos`: every combo row with its exact suits (call `gwCaptureSummary({ includeCombos: true })`; useful on the river, where suits matter).

Open the node, click **Summary** with no hand selected, then run the script: paste it into the browser console, or let Claude run it with the page JavaScript tool. It only reads the page; nothing is sent anywhere. Action names come back with their sizing label, e.g. `Allin 21 (207%)`. If GTO Wizard changes its page structure, the two selectors at the top of the script are what to update.

## Tips from building the examples

* **Always capture the response.** The single most common wrong explanation is reasoning about a bet without looking at how the opponent responds. In the river example, it looked like SB's chop hands shove to fold out LJ's chops; the response node showed LJ calls 83.7%, and the real reason only appeared on the check line.
* **Rewind the line for fractional weights.** A 0.22 weight on a nut-flush combo is the product of earlier-street frequencies (0.286 × 0.771). The rewind table shows which street removed it.
* **Check the numbers add up.** `python3 scripts/harness.py validate spot.json` flags action frequencies that don't sum to 100% and seat names that don't match the table. In the preflop example, the harness's card-removal maths reproduces GTO Wizard's 69.4% LJ fold frequency from the class rows, which is a good sign the capture is complete; when it doesn't match, a row is usually missing.
