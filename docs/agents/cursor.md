# Cursor

Status: **from docs**, not yet run live. Cursor runs Claude Code hooks from `.claude/settings.json` ([docs](https://cursor.com/docs/reference/third-party-hooks)) and reads skills from `.agents/skills`.

1. Do the [common setup](README.md#common-setup-every-agent-except-claude-code).
2. Add this to `.claude/settings.json`. The same block also works for Claude Code (including Claude Code on the web, which doesn't install plugins), GitHub Copilot CLI and Devin, so one file covers a mixed team.

```json
{
  "hooks": {
    "PreToolUse": [
      { "matcher": "Bash|Shell|exec|Edit|Write|MultiEdit|edit|write|create|apply_patch",
        "hooks": [{ "type": "command", "command": "\"$(command -v python3 || command -v python || command -v py)\" \"$(git rev-parse --show-toplevel)/.agents/scripts/pace.py\" guard", "timeout": 900 }] }
    ],
    "Stop": [
      { "hooks": [{ "type": "command", "command": "\"$(command -v python3 || command -v python || command -v py)\" \"$(git rev-parse --show-toplevel)/.agents/scripts/pace.py\" stop", "timeout": 10 }] }
    ],
    "SessionStart": [
      { "hooks": [{ "type": "command", "command": "\"$(command -v python3 || command -v python || command -v py)\" \"$(git rev-parse --show-toplevel)/.agents/scripts/pace.py\" session", "timeout": 10 }] }
    ]
  }
}
```

3. Make sure third-party hooks are on in Cursor's settings (they are by default).

## Cursor cloud agents

Cloud agents run `.cursor/hooks.json` from the repo; whether they also read `.claude/settings.json` isn't documented. Commit this as well:

```json
{
  "version": 1,
  "hooks": {
    "beforeShellExecution": [{ "command": "\"$(command -v python3 || command -v python)\" .agents/scripts/pace.py guard" }],
    "preToolUse": [{ "matcher": "Write", "command": "\"$(command -v python3 || command -v python)\" .agents/scripts/pace.py guard" }],
    "stop": [{ "command": "\"$(command -v python3 || command -v python)\" .agents/scripts/pace.py stop", "loop_limit": 1 }]
  }
}
```

And install the git hook on every build in `.cursor/environment.json`: `{ "install": "python3 .agents/scripts/pace.py install-git-hook" }`. See [cloud.md](cloud.md).

## How it maps

| pace needs | Cursor gives |
|---|---|
| Shell command | `PreToolUse` mapped to `preToolUse`; Claude's `Bash` arrives as `Shell`. `beforeShellExecution` sends `command` at the top level |
| Edited file path | `Edit`/`Write` arrive as `Write`. pace looks for `file_path`, `filePath` or `path`; Cursor's docs don't name the field |
| Reply text | Not available in `stop`, so the word cap doesn't run in Cursor |
| Block | exit code 2 |
