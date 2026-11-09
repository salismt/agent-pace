# Cursor

Status: **from docs**, not yet run live. Cursor runs Claude Code hooks from `.claude/settings.json` ([docs](https://cursor.com/docs/agent/third-party-hooks)) and reads skills from `.agents/skills`.

1. Do the [common setup](README.md#common-setup-every-agent-except-claude-code).
2. Add this to `.claude/settings.json`. The same block also works for Claude Code, GitHub Copilot CLI and Devin, so one file covers a mixed team.

```json
{
  "hooks": {
    "PreToolUse": [
      { "matcher": "Bash|Shell|exec|Edit|Write|MultiEdit|edit|write|create|apply_patch",
        "hooks": [{ "type": "command", "command": "python3 \"$(git rev-parse --show-toplevel)/.agents/scripts/pace.py\" guard", "timeout": 900 }] }
    ],
    "Stop": [
      { "hooks": [{ "type": "command", "command": "python3 \"$(git rev-parse --show-toplevel)/.agents/scripts/pace.py\" stop", "timeout": 10 }] }
    ]
  }
}
```

3. Make sure third-party hooks are on in Cursor's settings (they are by default).

## How it maps

| pace needs | Cursor gives |
|---|---|
| Shell command | `PreToolUse` mapped to `preToolUse`; Claude's `Bash` arrives as `Shell` |
| Edited file path | `Edit`/`Write` arrive as `Write`. pace looks for `file_path`, `filePath` or `path`; Cursor's docs don't name the field |
| Reply text | Not available in `stop`, so the word cap doesn't run in Cursor |
| Block | exit code 2 |

If you prefer Cursor's own `.cursor/hooks.json`, `pace.py guard` also accepts the `beforeShellExecution` payload (`command` at the top level).
