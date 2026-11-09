---
name: pace
description: Use to set up pace in a project ("turn on pace here", "add a claims ledger to this repo"), to see whether it helps ("pace stats", "is the word cap working", "how fast am I approving things"), to log review time after a task ("log review", "that review took me 15 minutes"), or when the user asks about moving pace from observe to enforce.
---

# pace

pace does nothing in a project until that project has `pace.toml` at its root. The script is `scripts/pace.py`, two folders above this skill's base directory; below, `pace.py` means `python3 <base>/../../scripts/pace.py`.

## Set up in a project
1. Confirm the project root with the user. Do not guess it from folder names.
2. `cp <base>/../../templates/pace.toml <root>/pace.toml`. After this, only the user edits it.
3. Suggest the user adds `.pace/log.jsonl` to `.gitignore`. `.pace/reviews.csv` can be committed.
4. Say: it starts in observe mode. Hooks log what they would block and block nothing.
5. **New project (greenfield):** offer the claims skill to write down the first promises as they are made.
   **Existing project (brownfield):** offer the claims skill's "Adopt in an existing codebase" steps, which start from `pace.py harvest`.

## Continue work on an existing project
When the user resumes work, or hands an existing project to a new agent or session:
1. The session-start hook already lists the promises in force and the last break. Read them before planning.
2. Run `pace.py check` before the first change, so a break that was already there isn't blamed on the new work.
3. If the project uses a spec-driven tool, read its spec and task files for the change, and tag the change's acceptance criteria for the comprehension gate.
4. If the user has been away, show `pace.py stats` and any breaks from `.pace/log.jsonl` since their last review, in 100 words or fewer.

## Stats
Run `pace.py stats` and report the numbers as printed, in 100 words or fewer. Do not interpret beyond the numbers.

## Log a review
After a task the user reviewed: `pace.py review --task "<task>" --minutes <N> --accepted yes|no`. The minutes come from the user. Never estimate them.

## Observe to enforce
Only the user changes `mode` in `pace.toml`. When asked, show the would-block events from `.pace/log.jsonl` (word-cap hits and continuity breaks, with dates) so the user can judge whether any were false stops.
