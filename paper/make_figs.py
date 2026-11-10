"""Paper figure: python3 make_figs.py -> figures/fixture_matrix.pdf

One panel per condition (never pooled, PREREGISTRATION.md changes 7 and 11), override tickets only.
Rows are fixtures, columns are arms; each cell shows runs broken / runs. The fixture is the unit of analysis,
and the figure shows why: cells are almost always all-or-nothing.
"""
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
BENCH = HERE.parent / "bench"
sys.path.insert(0, str(BENCH))
from analyze import ARMS, load  # noqa: E402
from export_tex import CONDS, fixture_cells  # noqa: E402

import matplotlib  # noqa: E402
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

TITLES = {"Claude": "Claude Code, Sonnet 5.5\n(round 1, default effort)",
          "ClaudeMed": "Claude Code, Sonnet 5.5\n(round 2, medium effort)",
          "CodexMed": "Codex CLI, GPT-6.1-Sol\n(round 2, medium effort)",
          "Codex": "Codex CLI, default model\n(round 1, incomplete)"}

runs = load(BENCH / "results" / "runs.jsonl")
order = ["Claude", "ClaudeMed", "CodexMed", "Codex"]
fxs = sorted({r["fixture"] for r in runs})
fig, axes = plt.subplots(1, len(order), figsize=(10, 3.0), sharey=True,
                         gridspec_kw={"width_ratios": [4, 3, 3, 3]})
for ax, tag in zip(axes, order):
    sub = [r for r in runs if (r["agent"], r["model"]) == CONDS[tag]]
    arms = [a for a in ARMS if any(r["arm"] == a and r["ticket"] == "override" for r in sub)]
    for j, a in enumerate(arms):
        c = fixture_cells(sub, "override", a)
        for i, fx in enumerate(fxs):
            k, n = c.get(fx, (0, 0))
            if not n:
                continue
            share = k / n
            ax.scatter(j, i, s=60 + 340 * share, color="#c0392b" if k else "white",
                       edgecolors="#c0392b" if k else "#9aa5b1", linewidths=1, zorder=2)
            ax.text(j + 0.32, i, f"{k}/{n}", va="center", fontsize=6.5, color="#333333")
    ax.set_xticks(range(len(arms)), arms, fontsize=8)
    ax.set_xlim(-0.5, len(arms) - 0.2)
    ax.set_title(TITLES[tag], fontsize=8)
    ax.invert_yaxis() if ax is axes[0] else None
    ax.grid(axis="y", color="#eeeeee", zorder=0)
    ax.spines[["top", "right", "left"]].set_visible(False)
    ax.tick_params(axis="y", length=0)
axes[0].set_yticks(range(len(fxs)), fxs, fontsize=8)
fig.suptitle("Override tickets: runs that broke an armed promise in a commit, per fixture", fontsize=9)
fig.tight_layout()
(HERE / "figures").mkdir(exist_ok=True)
fig.savefig(HERE / "figures" / "fixture_matrix.pdf")
fig.savefig(HERE / "figures" / "fixture_matrix.png", dpi=200)
print(f"figures/fixture_matrix.pdf from {len(runs)} runs")
