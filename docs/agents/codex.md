# OpenAI Codex CLI

Status: **tested live** (Codex CLI 0.159, November 2026): the edit to `pace.toml` and the commit breaking a claim were both blocked, and a 296-word reply was sent back and rewritten in 36 words.

Uses Codex hooks ([docs](https://developers.openai.com/codex/hooks)) and skills from `.agents/skills`.

1. Do the [common setup](README.md#common-setup-every-agent-except-claude-code).
2. Create `.codex/hooks.json`:

```json
{
  "hooks": {
    "PreToolUse": [
      { "matcher": "Bash|apply_patch",
        "hooks": [{ "type": "command", "command": "\"$(command -v python3 || command -v python || command -v py)\" \"$(git rev-parse --show-toplevel)/.agents/scripts/pace.py\" guard", "timeout": 900 }] }
    ],
    "Stop": [
      { "hooks": [{ "type": "command", "command": "\"$(command -v python3 || command -v python || command -v py)\" \"$(git rev-parse --show-toplevel)/.agents/scripts/pace.py\" stop", "timeout": 10 }] }
    ]
  }
}
```

3. Trust the hooks. Codex skips new or changed hooks until you review them: run `/hooks` in Codex. Project hooks also need the project itself to be trusted.

## Codex cloud

Codex cloud tasks don't run hooks from the repo. Use the git hook from the environment's setup script, plus the `AGENTS.md` lines in [other-agents.md](other-agents.md#rules-file-agents-without-skills):

```bash
python3 .agents/scripts/pace.py install-git-hook
```

See [cloud.md](cloud.md).

## How it maps

| pace needs | Codex gives |
|---|---|
| Shell command | `PreToolUse`, `tool_name: "Bash"`, `tool_input.command` |
| Edited file path | `tool_name: "apply_patch"`. pace reads the paths from the patch's `*** Update/Add/Delete File:` lines |
| Reply text | `Stop` → `last_assistant_message` |
| Block | exit code 2 with the reason on stderr; for Stop, `{"decision":"block","reason":…}` |
