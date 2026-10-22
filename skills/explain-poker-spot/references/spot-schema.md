# Spot file reference

A spot file is JSON describing one decision as GTO Wizard shows it. Only `module` and (postflop) `board` are required; every other block is optional, and each one you add unlocks more of the explanation. The report's **Coverage** section lists what's missing.

Frequencies can be written as percentages (`54.5`) or fractions (`0.545`). Stacks and pots are in big blinds.

## Top level

| Field | Type | Used for |
|---|---|---|
| `module` | `"preflop"` or `"postflop"` | Which explainer runs. |
| `title` | string | Report heading. |
| `source` | string | Where the numbers came from (solution, date). |
| `format` | object | Tournament context, see below. |
| `table` | list of `{seat, stack}` | Start-of-hand stacks, in seat order. |
| `hero`, `villain` | seat names | The two players being explained. Must match `table`. |
| `history` | list of `{street, board?, actions}` | Plain-text action so far. |
| `board` | `"KsJs6s8sQs"` | Postflop board (3-5 cards). |
| `pot` | number | Pot at the node, before the node's action. |
| `stacks_behind` | `{seat: bb}` | Stacks behind at the node. Committed chips = start stack − behind. |
| `bet` | `{size, pot_before}` | The bet or shove being explained, for break-even fold maths. |
| `node` | node object | The decision being explained. |
| `hero_hand` | hand row | The specific hand. |
| `hands` | list of hand rows | Grid or Summary rows for outlier detection. |
| `equity` | `{seat: {combos, equity, eqr, ev}}` | Equity chart tab. |
| `breakdown` | `{seat: [{category, pct, combos, strategy?}]}` | Breakdown tab. |
| `ranges` | `{seat: range}` | Ranges for card counting and blockers (see Ranges). |
| `ranges_partial` | list of seats | Ranges that only list some combos (e.g. just the strong ones). |
| `response` | node object | The opponent's node right after the hero's action. |
| `alternatives` | list of `{action?, line, steps: [node], note?}` | What happens after each of the hero's other actions. Set `action` to the action's GTO Wizard name (e.g. `"Raise 6"`) so the report can tell which actions still have no line. |
| `compare_hands` | list of hands | Preflop: hands to compare with the hero hand for card removal (defaults to the same-family neighbours, e.g. A5s and A3s for A4s). |
| `rewind` | object | Earlier-street frequencies, see below. |
| `icm_compare` | `{player?, chipev: actions, icm: actions, note?}` | Same node solved in ChipEV and ICM. |
| `blockers_tab` | object | Numbers from GTO Wizard's Blockers tab, e.g. `{"value_removal": 7, "trash_removal": 0}`. |
| `lesson` | string | Overrides the generated takeaway. |
| `notes` | list of strings | Caveats about the capture, printed with the lesson. |

## `format`

```json
{
  "game": "MTT",
  "structure": "9-max, 200 entrants",
  "phase": "50% of the field left",
  "icm": true,
  "payouts": [3000, 2000, 1400, 1000, 800],
  "players_left": 100,
  "average_stack": 50
}
```

`payouts` (1st place first) turns the ICM section from a qualitative note into numbers: bubble factors and the risk premium for any all-in call. For big fields, add `players_left` and `average_stack`; the harness models the players not at your table as average stacks (GTO Wizard uses the real ladder, so read these numbers as directional).

## Node object

```json
{
  "player": "LJ",
  "facing": "Allin 21",
  "actions": {"Call": 83.7, "Fold": 16.3},
  "combos": {"Call": 84.12, "Fold": 16.36},
  "pot_odds": 40.3,
  "hands": [hand rows],
  "breakdown": [{"category": "Flush", "pct": 16.3, "combos": 16.4}],
  "note": "free text shown under the node"
}
```

## Hand row

```json
{
  "hand": "AsTs",
  "label": "Royal flush",
  "weight": 0.5,
  "equity": 100,
  "strategy": {"Allin 21": 96.9, "Check": 3.1},
  "ev": {"Allin 21": 27.18, "Check": 27.09},
  "ev_best": 27.18
}
```

`hand` is a combo (`AsTs`) or a class (`A4s`, `KQo`, `77`). `ev` is per action (Hands tab hover); `ev_best` is the single EV column in the Summary tab. On postflop boards the harness labels rows itself ("Plays the board", "Top pair", "Flush draw") unless you give `label`.

## Ranges

Either text or a dict:

```json
"ranges": {
  "LJ": "AA, KK:0.5, AKs, A5s-A2s, 22+, KTo+, AsKh:0.22",
  "SB": {"AsTs": 0.5, "QQ": 1, "T9s": 0.68}
}
```

Supported tokens: classes (`AKs`, `AKo`, `AK`, `TT`), exact combos (`AsKh`), `22+`, `A2s+`, `KTo+`, dash ranges (`A9s-A2s`, `99-55`, `T9s-65s`), and `:weight` suffixes.

## `rewind`

```json
{
  "player": "LJ",
  "steps": ["Flop check", "Turn bet 2bb"],
  "rows": [
    {"hand": "AsAh", "label": "Nut flush", "freqs": [1.4, 99.2], "weight": 0.01}
  ]
}
```

`freqs` are the frequencies with which the combo took the line at each step. The product of the steps is how much of the combo reaches the node; `weight` is the weight GTO Wizard shows there. A mismatch usually means a missing step (most often the preflop open).
