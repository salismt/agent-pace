"""Figures for the paper from the primary (Claude Code + Sonnet) runs: python3 make_figs.py -> figures/broken_by_arm.pdf

Same plot as `bench/analyze.py --figs`, filtered to the primary agent (PREREGISTRATION.md, change 5).
"""
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
BENCH = HERE.parent / "bench"
sys.path.insert(0, str(BENCH))
from analyze import figures, load  # noqa: E402

runs = [r for r in load(BENCH / "results" / "runs.jsonl") if r["agent"] == "claude"]
figures(runs, HERE / "figures")
print(f"figures/broken_by_arm.pdf from {len(runs)} Claude runs")
