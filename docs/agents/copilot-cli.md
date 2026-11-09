# GitHub Copilot CLI

Status: **from docs**, not yet run live. Copilot CLI runs hooks from `.claude/settings.json` and `.github/hooks/*.json` ([docs](https://docs.github.com/en/copilot/reference/hooks-reference)), and reads skills from `.agents/skills`.

1. Do the [common setup](README.md#common-setup-every-agent-except-claude-code).
2. Add the `.claude/settings.json` block from [cursor.md](cursor.md). With the PascalCase `PreToolUse` event, Copilot sends Claude-style tool names and snake_case fields.

The Copilot **cloud** agent reads only `.github/hooks/*.json`. For it, use the [git pre-commit hook](other-agents.md#git-pre-commit-any-agent) instead.

## How it maps

| pace needs | Copilot CLI gives |
|---|---|
| Shell command | `PreToolUse`, `Bash`, `tool_input.command` |
| Edited file path | `Edit`/`Write`; pace looks for `file_path`, `filePath` or `path` |
| Reply text | `agentStop` gives a transcript path in Copilot's own format, so the word cap doesn't run |
| Block | exit code 2 |
