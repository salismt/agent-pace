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

## Claude Code on the web (cloud sessions)

Cloud sessions don't install plugins, but they run the repo's `.claude/settings.json` hooks. Commit `.agents/` from the [common setup](README.md#common-setup-every-agent-except-claude-code) and the `.claude/settings.json` block from [cursor.md](cursor.md). That block runs on your PC as well, so if your repo has it, you don't need the plugin. See [cloud.md](cloud.md).

## Without the plugin system

Use the [common setup](README.md#common-setup-every-agent-except-claude-code) and the `.claude/settings.json` block in [cursor.md](cursor.md). Claude Code reads it too.
