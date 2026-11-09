# OpenClaw

Status: **from source**, not yet run live. Built from OpenClaw's plugin hook source on GitHub (`main`, November 2026), and the plugin's handlers were tested with OpenClaw's event shapes (`exec`, `edit`, `apply_patch`, `before_agent_finalize`). OpenClaw itself wasn't installed for the test.

OpenClaw extends through JS plugins, so agent-pace ships one: [`adapters/openclaw/`](../../adapters/openclaw). It guards `exec`, `edit`, `write` and `apply_patch`, and applies the word cap before a reply is final. In a project without `.agents/scripts/pace.py` it does nothing.

1. Do the [common setup](README.md#common-setup-every-agent-except-claude-code), and copy the adapters too: `cp -R /tmp/agent-pace/adapters .agents/`.
2. Install and enable the plugin:

```bash
openclaw plugins install -l .agents/adapters/openclaw
openclaw plugins enable agent-pace
```

3. For the word cap, give the plugin access to the reply in `~/.openclaw/openclaw.json`:

```json
{ "plugins": { "entries": { "agent-pace": { "enabled": true, "hooks": { "allowConversationAccess": true } } } } }
```

4. Add the `AGENTS.md` lines from [other-agents.md](other-agents.md#rules-file-agents-without-skills) to your project, so the agent knows the promises at the start of a session.

## How it maps

| pace needs | OpenClaw gives |
|---|---|
| Shell command | `before_tool_call`, `toolName: "exec"`, `params.command`, `params.workdir` |
| Edited file path | `edit` / `write`, `params.path`; `apply_patch`, the paths inside `params.input` |
| Reply text | `before_agent_finalize`, `lastAssistantMessage`; returns `{action: "revise"}`, once (`stopHookActive`) |
| Block | the handler returns `{ block: true, blockReason }` |

## Limits

- OpenClaw blocks a tool call whose hook runs longer than 15 s. The plugin gives `pace.py` 12 s, so keep claim checks fast.
- The tool hook has no working directory. The plugin uses `exec`'s `workdir`, then the session's workspace, then the gateway's own folder. If your repo isn't the OpenClaw workspace, edits outside it may not find `pace.toml`; the git hook still catches the commit.
