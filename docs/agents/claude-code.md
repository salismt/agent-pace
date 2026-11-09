# Claude Code

Status: **tested live** (Claude Code, November 2026).

## Install as a plugin (one project)

```bash
claude plugin marketplace add salismt/agent-pace --scope project
claude plugin install agent-pace@agent-pace --scope project
```

Always pass `--scope project`. The default scope is `user`, which loads the plugin in every project. pace is inert without `pace.toml`, but there's no reason to load it everywhere.

Then tell Claude: **"turn on pace here"**. The `pace` skill copies the starting `pace.toml` into your project root.

## What the plugin adds

| Piece | Where |
|---|---|
| Guard on `Edit`, `Write`, `MultiEdit`, `NotebookEdit`, `Bash` | `hooks/hooks.json` → `pace.py guard` |
| Word cap at the end of each reply | `hooks/hooks.json` → `pace.py stop` |
| Skills `agent-pace:claims`, `agent-pace:comprehension-gate`, `agent-pace:pace` | `skills/` |

## Turn it off

```bash
claude plugin disable agent-pace@agent-pace --scope project
```

Or delete `pace.toml`.

## Without the plugin system

Use the [common setup](README.md#common-setup-every-agent-except-claude-code) and the `.claude/settings.json` block in [cursor.md](cursor.md). Claude Code reads it too.
