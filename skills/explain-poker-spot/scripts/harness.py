#!/usr/bin/env python3
"""Run the poker explainability harness from inside the skill folder.

    python3 harness.py explain spot.json [--format md|json|brief] [-o OUT]
    python3 harness.py validate spot.json
    python3 harness.py check spot.json explanation.md
    python3 harness.py board KsJs6s8sQs
    python3 harness.py icm --stacks 40 30 20 10 --payouts 50 30 20 --hero 3 --villain 0

No install and no dependencies: it adds this folder to the import path.
"""

import sys
from pathlib import Path

if sys.version_info < (3, 10):
    sys.exit("The poker harness needs Python 3.10 or newer.")

sys.path.insert(0, str(Path(__file__).resolve().parent))

from poker_harness.cli import main  # noqa: E402

if __name__ == "__main__":
    raise SystemExit(main())
