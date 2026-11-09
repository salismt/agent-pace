---
name: comprehension-gate
description: Use when an agent-built feature must be understood by the user before they accept it - while writing acceptance criteria, after tests pass, and at handoff (it pairs with spec- or PRD-driven workflows that keep acceptance criteria in a coverage-contract.json). Also use when the user says "walk me through it", "do I actually understand this", "explain what changed", or approves a large change within seconds.
---

# Comprehension gate

The user accepts a core change only after they can explain it. Throwaway work skips the gate. The script is `scripts/pace.py`, two folders above this skill's base directory.

## 0. No coverage-contract.json yet (existing projects)
For a change in an existing codebase, write a small `coverage-contract.json` next to the change's spec or task file, with one item per acceptance criterion of this change only:
```json
{"acceptance": [{"id": "AC-01", "tier": "core"}, {"id": "AC-02", "tier": "throwaway"}]}
```
If a spec-driven tool already numbers the requirements (for example `REQ-3` or a task id), reuse those ids. Never cover the whole legacy codebase: only what this change touches.

## 1. Tag each acceptance criterion
In `coverage-contract.json`, add `"tier": "core"` or `"tier": "throwaway"` to every item in `acceptance[]` (each item needs an `id`, for example `AC-03`).
- **Core:** data model, personal-data flows, core business logic, auth, payments, and anything a `pace.toml` claim touches.
- **Throwaway:** copy, layout, prototype-only scaffolding.
- An untagged item counts as core. Ask the user about the borderline ones in a single question that lists them.

## 2. Write a walkthrough per core criterion (after the tests pass)
Write `walkthroughs/<AC-id>.md` next to the contract, in 150 words or fewer:
```markdown
# AC-03: <title>
## What the user does
1. ... 2. ... 3. ...
## What changed in the code
- path/to/file: one line each
## What could go wrong
The riskiest assumption, in one sentence.
## How we know
Test name and evidence path.
## Explain-back
```
Leave `## Explain-back` empty.

## 3. Explain-back before reading (at handoff)
Before the user opens a walkthrough, ask once per core criterion:
"In one or two sentences: what does AC-03 do now, and what could go wrong?"
- Record the user's words **verbatim** under `## Explain-back`, with the date. Never write or paraphrase it yourself.
- Compare the answer to the walkthrough. List at most 3 gaps.
- If there is a gap on a core criterion, walk through only that part, then ask again.

## 4. Run the gate
`python3 <base>/../../scripts/pace.py gate --contract <path>/coverage-contract.json`
Each core criterion prints `no walkthrough`, `awaiting explain-back` or `explained`. Call the work ready for review only on exit 0.
