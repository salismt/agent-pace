# Pi

Status: **tested live** (Pi 0.85.1, `@earendil-works/pi-coding-agent`, November 2026) end to end with Pi's scripted `faux` model: the promises were added at session start, `git commit` was blocked on a break, a `write` to `pace.toml` was blocked, a plain command ran, and a 40-word reply was sent back once and answered in two words.

Pi extends through TypeScript extensions, so agent-pace ships one: [`adapters/pi/pace.ts`](../../adapters/pi/pace.ts). It is a project extension, so it runs only in this repo.

1. Do the [common setup](README.md#common-setup-every-agent-except-claude-code). Pi reads skills from `.agents/skills`.
2. Copy the extension:

```bash
mkdir -p .pi/extensions && cp /tmp/agent-pace/adapters/pi/pace.ts .pi/extensions/
```

3. Trust the project when Pi asks. Project extensions don't load until you do. Non-interactive runs (`pi -p`) need `--approve`.

## How it maps

| pace needs | Pi gives |
|---|---|
| Shell command | `tool_call`, `toolName: "bash"`, `input.command` |
| Edited file path | `write` / `edit`, `input.path` |
| Reply text | `agent_end`, the last assistant message; sent back once with `pi.sendUserMessage` |
| Session start | `before_agent_start` adds a hidden message once per session |
| Block | the handler returns `{ block: true, reason }` |
