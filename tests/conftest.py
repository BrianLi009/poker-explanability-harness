import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SKILL = ROOT / "skills" / "explain-poker-spot"
sys.path.insert(0, str(SKILL / "scripts"))
