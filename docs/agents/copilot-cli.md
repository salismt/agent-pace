# GitHub Copilot CLI and Copilot coding agent

Status: **from docs**, not yet run live. Skills are read from `.agents/skills`.

## Copilot CLI (your PC)

Copilot CLI runs hooks from `.claude/settings.json` and `.github/hooks/*.json` ([docs](https://docs.github.com/en/copilot/reference/hooks-reference)).

1. Do the [common setup](README.md#common-setup-every-agent-except-claude-code).
2. Add the `.claude/settings.json` block from [cursor.md](cursor.md). With the PascalCase `PreToolUse` event, Copilot sends Claude-style tool names and snake_case fields.

## Copilot coding agent (cloud)

The cloud agent reads only `.github/hooks/*.json`, and only from the default branch ([docs](https://docs.github.com/en/copilot/how-tos/copilot-on-github/customize-copilot/customize-cloud-agent/use-hooks)). Commit `.github/hooks/agent-pace.json`:

```json
{
  "version": 1,
  "hooks": {
    "preToolUse": [
      { "type": "command", "bash": "\"$(command -v python3 || command -v python)\" .agents/scripts/pace.py guard", "cwd": ".", "timeoutSec": 900 }
    ]
  }
}
```

Then install the git hook in `.github/workflows/copilot-setup-steps.yml` (see [cloud.md](cloud.md#setup-script-examples)).

## How it maps

| pace needs | Copilot gives |
|---|---|
| Shell command | CLI: `PreToolUse`, `Bash`, `tool_input.command`. Cloud: `preToolUse`, `toolName: "bash"`, `toolArgs` |
| Edited file path | `edit` / `create`; pace looks for `file_path`, `filePath` or `path` (the docs don't name the field) |
| Reply text | `agentStop` gives a transcript path in Copilot's own format, so the word cap doesn't run |
| Block | exit code 2 |
