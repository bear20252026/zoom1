#!/bin/sh
# Join the whole chain again from the model outputs already on disk (fast: the registered outputs are cached),
# then print the checks. Usage: tools/rejoin.sh
cd "$(dirname "$0")/.." || exit 1
for k in $(seq 1 34); do
  PYTHONDONTWRITEBYTECODE=1 python3 -W ignore tools/chain.py redo $k 2>&1 | grep -E "Traceback|Error"
done
PYTHONDONTWRITEBYTECODE=1 python3 -W ignore tools/qa.py
