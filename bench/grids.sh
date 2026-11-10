#!/usr/bin/env bash
# Second-round grids (PREREGISTRATION.md changes 7, 10, 11). Safe to rerun: finished runs are skipped,
# and runs lost to an account usage limit are not recorded, so the same command resumes after the reset.
#   bash bench/grids.sh codex     bash bench/grids.sh claude
set -u
cd "$(dirname "$0")"
case "$1" in
  codex)  agent=codex;  model="codex=gpt-6.1-sol@medium" ;;
  claude) agent=claude; model="claude=sonnet@medium" ;;
  *) echo "usage: $0 codex|claude"; exit 2 ;;
esac
log="results/grid-$1.log"
python3 run.py --matrix --agents "$agent" --models "$model" --tickets base,override --arms prose,hook,pace \
  --rep-start 0 --reps 2 --jobs 4 >> "$log" 2>&1
python3 run.py --matrix --agents "$agent" --models "$model" --tickets override --arms prose,hook,pace \
  --rep-start 2 --reps 2 --jobs 4 >> "$log" 2>&1
python3 - "$1" <<'PY' >> "$log"
import json, sys
m = {"codex": "gpt-6.1-sol@medium", "claude": "sonnet@medium"}[sys.argv[1]]
n = sum(json.loads(l)["model"] == m for l in open("results/runs.jsonl"))
print(f"GRID {sys.argv[1]}: {n}/108 recorded" + ("" if n >= 108 else " - rerun this script to resume"))
PY
