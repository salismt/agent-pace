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
5. Offer the claims skill to add the first claim.

## Stats
Run `pace.py stats` and report the numbers as printed, in 100 words or fewer. Do not interpret beyond the numbers.

## Log a review
After a task the user reviewed: `pace.py review --task "<task>" --minutes <N> --accepted yes|no`. The minutes come from the user. Never estimate them.

## Observe to enforce
Only the user changes `mode` in `pace.toml`. When asked, show the would-block events from `.pace/log.jsonl` (word-cap hits and continuity breaks, with dates) so the user can judge whether any were false stops.
