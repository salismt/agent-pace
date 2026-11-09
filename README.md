# agent-pace

**Let your agents run. Get interrupted only when they break a promise you made.**

A plugin for Claude Code, Codex, Gemini CLI, Cursor, Copilot CLI and Devin, for people who delegate more code than they can read.

[Install](#install) · [New project](#greenfield-start-a-new-project-with-promises) · [Existing codebase](#brownfield-add-agent-pace-to-an-existing-codebase) · [With Spec Kit, OpenSpec, BMAD and others](#with-spec-driven-development-tools) · [Limits](#known-limits)

## The problem

Agents now write code faster than you can understand it. So you approve it without reading.

In my own Claude Code transcripts (60 days, 1,355 replies after an agent output of 150 words or more), **20% of my replies came faster than I could have skimmed the output**. The median agent output before I replied was 396 words.

That has a cost. In [Anthropic's randomized trial](https://www.anthropic.com/research/AI-assistance-coding-skills), developers who learned a new library with AI help scored **50%** on a comprehension quiz, against **67%** for those who coded by hand. The biggest gap was in debugging.

More approval gates don't fix this; you approve them without reading too. pace takes the other way out: **stop asking for your attention on everything, and spend it only where a mistake would break something you promised.**

## What it does

| | |
|---|---|
| **Claims ledger** | `pace.toml` lists promises the code must keep, such as "we never store card numbers" or "customer data stays in the EU". Each promise has a check. Every `git commit`, `push`, `merge` and `gh pr create/merge` by an agent replays all of them. |
| **Continuity break** | A failing check is the only thing that stops the agent. It quotes your promise, names who you made it to, and stops. |
| **Owner-only files** | Agents can't edit `pace.toml` or an existing check. They can't "fix the test" to get past you. |
| **Reply word cap** | A final reply over 150 words goes back once with "put the detail in a file". |
| **Comprehension gate** | Core acceptance criteria need a walkthrough, and your own explanation in your own words, before the work counts as ready. |
| **Stats** | `pace.py stats` shows how fast you approve compared with how long the output takes to read. |

## What a break looks like

A real run (Claude Haiku 5.5, enforce mode, cap set to 60 words). The agent was told to edit `pace.toml`, add a `card_number` column and commit, then explain in 300 words:

```text
> Edit pace.toml
  pace: pace.toml is owner-only. Show the change as a TOML block for the user to paste.

> git add -A && git commit -m 'add card column'
  pace: continuity break. This change contradicts a promise in pace.toml:
  - C1: "We never store card numbers." (said to customers, PCI assessor).
    Check output: card_number column found in src/
  Do not edit the claim or its check. Tell the user in one line which change caused it, then stop.

> (296-word explanation)
  pace: your reply is 296 words; the cap here is 60. Put the detail in a file and reply again
  in 60 words or fewer: the result, one question, or the blocker.

Final reply (31 words):
  Blocked: the commit. The `card_number` column contradicts claim C1 ("We never store card
  numbers."). Nothing committed.
  Question: should I drop `card_number`, or use a tokenised value?
```

Nothing was committed, and `pace.toml` was left untouched. That one question is the only thing that needs you.

The same run in OpenAI Codex CLI 0.159 gave the same three blocks: the `apply_patch` edit to `pace.toml`, the commit, and the 296-word reply, rewritten in 36 words.

## Install

**Claude Code**, in the project you want it in:

```bash
claude plugin marketplace add salismt/agent-pace --scope project
claude plugin install agent-pace@agent-pace --scope project
```

Then tell Claude: **"turn on pace here"**. It copies a starting `pace.toml` into the project root, in observe mode. Always pass `--scope project`; the default is `user`, which means every project you open.

**Other agents:** copy three folders into `.agents/` and add one hook config. See the guide for yours:

| Agent | Guide | Status |
|---|---|---|
| Claude Code | [docs/agents/claude-code.md](docs/agents/claude-code.md) | tested live |
| OpenAI Codex CLI | [docs/agents/codex.md](docs/agents/codex.md) | tested live |
| Gemini CLI | [docs/agents/gemini-cli.md](docs/agents/gemini-cli.md) | from docs |
| Cursor | [docs/agents/cursor.md](docs/agents/cursor.md) | from docs |
| GitHub Copilot CLI | [docs/agents/copilot-cli.md](docs/agents/copilot-cli.md) | from docs |
| Devin (formerly Windsurf) | [docs/agents/devin.md](docs/agents/devin.md) | from docs |
| OpenCode, Amp, Cline, anything with git | [docs/agents/other-agents.md](docs/agents/other-agents.md) | git hook |

What each agent supports: [docs/agents/README.md](docs/agents/README.md).

Needs Python 3.11+ (for `tomllib`). No other dependencies, no network calls.

## Greenfield: start a new project with promises

A new project has no legacy, so the ledger can grow with every promise you make.

1. **Day one:** install, then tell your agent "turn on pace here". Leave `mode = "observe"` for the first week, then switch to `enforce`. With no legacy code, false breaks are rare.
2. **Write promises down as you make them.** Each sentence you put in a pitch deck, privacy policy, customer contract or partner agreement goes into the ledger, for example "customer data stays in the EU" or "no payout runs without human approval". Tell your agent; the `claims` skill writes the check and proves it fails on a violation.
3. **Gate the core work.** When an agent builds a feature from a spec or PRD, the `comprehension-gate` skill tags each acceptance criterion core or throwaway. Core ones need a walkthrough and your own explain-back before the work counts as ready.
4. **Watch your approval speed.** `pace.py stats` shows how often you reply faster than you could read. If that number stays high, lower `word_cap`.

## Brownfield: add agent-pace to an existing codebase

An existing codebase already holds promises, scattered through specs, security and privacy docs, ADRs and READMEs. Some are already broken. agent-pace starts from what is written down and treats existing breaks separately from new ones.

### Adopt it in four steps

1. **Harvest what you've already promised.**
   ```bash
   python3 <plugin>/scripts/pace.py harvest          # strong wording: never, must not, SHALL, MUST, guarantee
   python3 <plugin>/scripts/pace.py harvest --all    # adds must, always, only
   ```
   It lists sentences with promise wording, spec-tool files first, and marks the ones already in the ledger. It writes nothing. On a real 70-file codebase it found 321 candidates; most were internal conventions, which belong in a rules file. Keep only promises made to someone outside the code.
2. **Turn the chosen ones into claims.** Tell your agent "adopt pace in this codebase". The `claims` skill groups the candidates by who the promise was made to and asks you once which ones are real. Then it writes the checks, reusing existing tests where it can.
3. **Baseline the current main branch.** Run `pace.py check`. A claim that already fails on existing code is not a new break. Either fix it first, or record it:
   ```toml
   [[claim]]
   id = "C3"
   said = "Card numbers are never written to logs."
   to = "PCI assessor"
   known_break = "legacy payment worker logs raw requests; removal tracked in PAY-123"
   ```
   A known break is shown on every check but never blocks. When its check starts passing, `check` tells you to remove the line.
4. **Observe for two weeks, then enforce.** `.pace/log.jsonl` shows every would-be block, so you can spot false breaks before they cost anyone a stopped commit.

### Continue work on an existing project

Most brownfield work isn't adoption. It's picking up where you, a teammate or another agent left off.

- **The promises travel with the repo.** `pace.toml` and `claims/checks/` are in git, so every agent, session and teammate gets the same ledger, whichever agent tool they use.
- **New sessions hear the rules first.** The Claude Code plugin's session-start hook (`pace.py session`) tells a new or resumed agent which promises are in force, which are known breaks, and when the last break happened. For other agents, add the `AGENTS.md` lines in [other-agents.md](docs/agents/other-agents.md#rules-file-agents-without-skills). In a live Claude Code test, an agent told to add a `card_number` column read C1 at session start and stopped before editing anything: "Adding `card_number TEXT` would break C1. Should I add a token or last-4 column instead?"
- **Check before the first change.** The agent runs `pace.py check` before it touches anything, so a break that was already there isn't blamed on the new work.
- **Gate only what the change touches.** For a change in legacy code, the agent writes a small `coverage-contract.json` with this change's acceptance criteria only, reusing your spec tool's requirement ids. You explain those back, not the whole codebase.
- **Catch up after time away.** Ask "what happened while I was away?". The `pace` skill shows `stats` and every break since your last review, in 100 words or fewer.

### With spec-driven development tools

Spec-driven tools write your non-negotiables down. **agent-pace makes them stop a commit.** We read the docs of the five most-starred AI development methods, plus Kiro. Each keeps requirements in files and checks them inside the agent session, if at all. None of them blocks a commit when a requirement breaks; that is the gap agent-pace fills. `harvest` reads all of their requirement files.

| Method (GitHub stars, 9 Nov 2026) | Where its non-negotiables live | Its brownfield entry point | How agent-pace fits |
|---|---|---|---|
| [Superpowers](https://github.com/obra/superpowers) (315k) | `docs/superpowers/specs/`, `docs/superpowers/plans/` | The brainstorming skill explores the existing project first | `harvest` reads the design specs and plans. The constraints in them that customers or regulators rely on become claims. Both tools' session-start hooks run side by side. |
| [GitHub Spec Kit](https://github.com/github/spec-kit) (149k) | `.specify/memory/constitution.md`; `specs/NNN-feature/spec.md` (`FR-001: System MUST …`) | `specify init --here`, then `/speckit-constitution` with principles already true for the repo | The Constitution Check runs once, when the plan is made. agent-pace re-checks the outward-facing principles on every commit. Reuse `FR-001` as the acceptance id in the comprehension gate. |
| [OpenSpec](https://github.com/Fission-AI/OpenSpec) (74k) | `openspec/specs/<capability>/spec.md` and `openspec/changes/` (`SHALL` / `MUST`) | Write specs only for what you're about to change | Each change's `SHALL` lines that touch a promise become claims, and they stay enforced after `/opsx:archive`. |
| [GSD](https://github.com/gsd-build/get-shit-done) (64k, legacy repo) | `.planning/REQUIREMENTS.md`, `.planning/PROJECT.md` | `/gsd-map-codebase` records existing behaviour as "Validated" | Validated requirements that are promises become claims. Known gaps go in as `known_break`. |
| [BMAD Method](https://github.com/bmad-code-org/BMAD-METHOD) (55k) | `_bmad-output/prd-*/` (`FR-N`, `RULE-N`) | `bmad-project-context`, then `bmad-build` | `RULE-N` items ("everything below must obey") are the closest to claims. |
| [Kiro](https://kiro.dev) (250k+ users, 2025) | `.kiro/steering/`, `.kiro/specs/*/requirements.md` (EARS: `WHEN … THE SYSTEM SHALL …`) | "Generate Steering Docs" from the existing project | `SHALL` requirements that are outward promises become claims. Kiro's hooks run inside the session; agent-pace adds the check at commit time. |

Requirement files and phrasing are taken from each project's own docs. We haven't run agent-pace alongside each of these tools yet. Reports are welcome.

## A promise's life

1. **You say it:** "We never store card numbers."
2. **The agent compiles it** into `claims/checks/C1.sh`: the cheapest faithful check, such as a test, a grep or Semgrep rule, a config assertion, or a probe against the running app.
3. **The agent proves the check bites.** It makes a deliberate violation in a throwaway worktree, and the check must fail. A check that can't be made to fail is reported as weak.
4. **You paste the claim into `pace.toml`.** Only you can.
5. **Every commit, push and PR replays the ledger.** On a break, you decide: revert the change, or change the promise and tell whoever you made it to.

```toml
[pace]
mode = "observe"   # log what would block; "enforce" blocks
word_cap = 150

[[claim]]
id = "C1"
said = "We never store card numbers."
to = "customers, PCI assessor"
since = "2026-11-09"
cosign = ""        # someone who must agree, for example a domain expert
# known_break = "why, and the ticket"   # an existing violation you accept for now; reported, never blocks
```

## Built to limit its own damage

| Property | How |
|---|---|
| Inert by default | Does nothing in a project without `pace.toml`. |
| Observe first | New installs log what they would block and block nothing. Only you switch to `enforce`. |
| Fails open | A crash or a broken `pace.toml` never blocks work. The error is logged and counted in `stats`. |
| Agents can't loosen it | Mode, claims and existing checks all live in owner-only files, and `git commit --no-verify` is blocked. |
| Checks are files | Each check is a file in git, run without a shell, so every one can be reviewed and diffed. |
| One switch | Disable the plugin, or delete `pace.toml`. |

## Commands

```bash
python3 <plugin>/scripts/pace.py check        # one line per claim: holds | BREAK | known-break | error | uncompiled
python3 <plugin>/scripts/pace.py harvest      # brownfield: promise-like sentences already in specs and docs
python3 <plugin>/scripts/pace.py stats        # approval speed, word-cap hits, breaks, review minutes
python3 <plugin>/scripts/pace.py gate --contract coverage-contract.json
python3 <plugin>/scripts/pace.py review --task PRD-7 --minutes 12 --accepted yes
python3 <plugin>/scripts/pace.py pre-commit   # git hook for any agent
```

The skills call these for you: `pace`, `claims` and `comprehension-gate`.

## Why TOML

The ledger is a list of promises, not logic; the logic lives in the check files. So the ledger needs a data format people can edit and diff, not a DSL. TOML has comments, has no indentation traps (YAML reads `NO` as false), and Python reads it with the standard library. JSON has no comments, and YAML needs a dependency.

## Known limits

- The shell guard is a regex. It stops `>`, `sed -i`, `rm`, `mv`, `cp`, `tee`, `git checkout/restore` and Python `open(..., 'w')` on protected paths, but a script written elsewhere and then run can still write to them. Git history of `pace.toml` is the backstop.
- A check is only as good as its probe. That's why the agent must show each new check failing on a deliberate violation.
- pace can't tell whether an explain-back was paraphrased.
- Checks run in the agent's local environment. A check that needs services that aren't running fails. Observe mode is where you find those false breaks.

## Where the idea comes from

- Donella Meadows, *Thinking in Systems*: speeding up your reaction to delayed feedback makes the system swing harder. Change the structure, not the speed.
- Peter Senge, *The Fifth Discipline*: "faster is slower", and shifting the burden to a quick fix weakens the real fix.
- DeepSeek's [dsh-superagent prototype](https://github.com/deepseek-ai/dsh-superagent-prototype): treat human attention as a budget, enforced in code.

## Develop

```bash
python3 tests/test_pace.py
claude plugin validate plugin
```

`plugin/` is what installs. Tests and docs stay outside it.

MIT licensed.
