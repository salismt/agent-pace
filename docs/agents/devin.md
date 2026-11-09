# Devin Desktop and Devin CLI (formerly Windsurf)

Status: **from docs**, not yet run live. Devin runs hooks from `.claude/settings.json` or `.devin/hooks.v1.json` ([docs](https://docs.devin.ai/cli/extensibility/hooks/overview)), and reads skills from `.agents/skills`.

1. Do the [common setup](README.md#common-setup-every-agent-except-claude-code).
2. Add the `.claude/settings.json` block from [cursor.md](cursor.md). Its matcher already includes Devin's tool names (`exec`, `edit`, `write`, `apply_patch`).

## How it maps

| pace needs | Devin gives |
|---|---|
| Shell command | `PreToolUse`, `tool_name: "exec"`, `tool_input.command` |
| Edited file path | `edit`/`write`; pace looks for `file_path`, `filePath` or `path` |
| Reply text | `Stop` gives only `stop_hook_active`, so the word cap doesn't run |
| Block | exit code 2 |
