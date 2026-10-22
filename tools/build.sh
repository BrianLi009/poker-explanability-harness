#!/usr/bin/env bash
# Build installable bundles into dist/:
#   dist/poker-explainer.plugin    Claude app plugin (open it in Claude, or drag it in)
#   dist/explain-poker-spot.zip    standalone skill (claude.ai Settings > Capabilities > Skills > Upload)
set -euo pipefail
cd "$(dirname "$0")/.."
rm -rf dist && mkdir -p dist
find . -name __pycache__ -prune -exec rm -rf {} +

zip -qr dist/poker-explainer.plugin .claude-plugin skills README.md LICENSE \
  -x "*.DS_Store" -x "*/__pycache__/*" -x ".claude-plugin/marketplace.json"
(cd skills && zip -qr ../dist/explain-poker-spot.zip explain-poker-spot -x "*.DS_Store" -x "*/__pycache__/*")

ls -l dist
