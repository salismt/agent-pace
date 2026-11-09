# Gemini CLI

Status: **from docs**, not yet run live. Uses Gemini CLI hooks ([docs](https://github.com/google-gemini/gemini-cli/blob/main/docs/hooks/index.md)) and skills from `.agents/skills`.

1. Do the [common setup](README.md#common-setup-every-agent-except-claude-code).
2. Add this to `.gemini/settings.json` (merge it with any `hooks` you already have). Timeouts are in milliseconds.

```json
{
  "hooks": {
    "BeforeTool": [
      { "matcher": "run_shell_command|write_file|replace",
        "hooks": [{ "type": "command", "command": "python3 \"$GEMINI_PROJECT_DIR/.agents/scripts/pace.py\" guard", "timeout": 900000 }] }
    ],
    "AfterAgent": [
      { "hooks": [{ "type": "command", "command": "python3 \"$GEMINI_PROJECT_DIR/.agents/scripts/pace.py\" stop", "timeout": 10000 }] }
    ]
  }
}
```

## How it maps

| pace needs | Gemini CLI gives |
|---|---|
| Shell command | `BeforeTool`, `tool_name: "run_shell_command"`, `tool_input.command` |
| Edited file path | `write_file` / `replace`, `tool_input.file_path` |
| Reply text | `AfterAgent` → `prompt_response` |
| Block | exit code 2 with the reason on stderr; for AfterAgent, `{"decision":"deny","reason":…}` |
