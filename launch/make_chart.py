"""README results chart, light and dark: python3 launch/make_chart.py -> docs/results-{light,dark}.svg

Override tickets, runs that broke a stated promise in a commit, per setup and arm. Drawn from bench/results/runs.jsonl.
"""
import json
from html import escape
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SETUPS = [("Claude Code · Sonnet 5.5", "claude", "sonnet"),
          ("Claude Code · Sonnet 5.5, medium effort", "claude", "sonnet@medium"),
          ("Codex CLI · GPT-6.1-Sol, medium effort", "codex", "gpt-6.1-sol@medium")]
ARMS = [("prose", "Promise in AGENTS.md"), ("hook", "Plain pre-commit hook"), ("pace", "agent-pace")]
THEMES = {"light": dict(bg="#ffffff", ink="#1f2328", muted="#59636e", grid="#d1d9e0", track="#eff2f5", red="#d1242f", green="#1a7f37"),
          "dark": dict(bg="#0d1117", ink="#f0f6fc", muted="#9198a1", grid="#3d444d", track="#151b23", red="#f85149", green="#3fb950")}


def counts():
    runs = [json.loads(l) for l in open(ROOT / "bench" / "results" / "runs.jsonl") if l.strip()]
    out = {}
    for _, agent, model in SETUPS:
        for arm, _ in ARMS:
            sub = [r for r in runs if (r["agent"], r["model"], r["ticket"], r["arm"]) == (agent, model, "override", arm)]
            out[(model, arm)] = (sum(bool(r["broken_head"]) for r in sub), len(sub))
    return out


def svg(theme, c):
    t = THEMES[theme]
    W, left, barw, rowh, gap = 880, 250, 420, 30, 26
    H = 58 + len(SETUPS) * (len(ARMS) * rowh + gap) + 20
    s = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img">',
         "<title>Override tickets: runs that broke a stated promise in a commit, per setup and arm</title>",
         f'<rect width="{W}" height="{H}" fill="{t["bg"]}"/>',
         f'<g font-family="-apple-system,Segoe UI,Helvetica,Arial,sans-serif" font-size="15" fill="{t["ink"]}">',
         f'<text x="0" y="22" font-size="17" font-weight="600">A teammate says the promise is out of date. Did the agent break it?</text>',
         f'<text x="0" y="44" fill="{t["muted"]}">Runs that broke a stated promise in a commit, PromiseBench override tickets</text>']
    y = 70
    for label, _, model in SETUPS:
        s.append(f'<text x="0" y="{y + 4}" font-weight="600">{escape(label)}</text>')
        y += 12
        for arm, name in ARMS:
            k, n = c[(model, arm)]
            share = k / n if n else 0
            col = t["green"] if arm == "pace" else t["red"]
            s.append(f'<text x="{left - 12}" y="{y + 15}" text-anchor="end" fill="{t["muted"]}">{escape(name)}</text>')
            s.append(f'<rect x="{left}" y="{y + 3}" width="{barw}" height="16" rx="3" fill="{t["track"]}"/>')
            if k:
                s.append(f'<rect x="{left}" y="{y + 3}" width="{barw * share:.1f}" height="16" rx="3" fill="{col}"/>')
            else:
                s.append(f'<rect x="{left}" y="{y + 3}" width="3" height="16" fill="{col}"/>')
            s.append(f'<text x="{left + barw + 12}" y="{y + 16}" font-weight="600" fill="{col if arm == "pace" else t["ink"]}">{k}/{n}</text>')
            y += rowh
        y += gap - 12
    s.append("</g></svg>\n")
    return "\n".join(s)


if __name__ == "__main__":
    c = counts()
    for theme in THEMES:
        p = ROOT / "docs" / f"results-{theme}.svg"
        p.write_text(svg(theme, c))
        print("wrote", p)
