---
name: claims
description: Use when the user states a promise the system must keep true for someone outside the code (a regulator, customers, a partner, a cofounder) - for example "customer data never leaves the EU region", "we never store card numbers", "no payout runs without a human approval", "medical codes never change without clinician sign-off" - or asks to add, compile or check a claim, asks "do we still keep our promises?", or when a "pace: continuity break" message appears. Works only in a project with pace.toml.
---

# Claims ledger

`pace.toml` lists the promises the user has made outside the code. Each claim has a check. When an agent commits, pushes, merges or opens a PR, the pace hook runs every check. A failing check is a **continuity break**: the system now contradicts a promise. That is the only reason this plugin interrupts the user.

The script is `scripts/pace.py`, two folders above this skill's base directory: `python3 <base>/../../scripts/pace.py check`.

## Rules (the hook enforces them)
- `pace.toml` is owner-only. Never edit it. Show changes as a TOML block for the user to paste.
- Never edit an existing file in `claims/checks/`. A check that fails is news, not a bug to fix.
- Never set `mode`. Only the user moves observe to enforce.

## Add a claim
1. Quote the user's sentence exactly. If one word changes what the check must test (for example "never leaves the EU": stored only, or processed too?), ask that one question. Otherwise continue.
2. Pick the cheapest check that is faithful to the sentence, in this order: an existing test or script; a grep or Semgrep rule over the code; a config assertion (for example a Terraform region); a probe against the running app.
3. Write it as a **new** file `claims/checks/<id>.sh` or `.py` with the Write tool. Exit 0 = holds. Non-zero = break, after printing one line that says what broke.
4. Prove it bites. In a throwaway git worktree, make a small change that violates the claim, run the check, and confirm it fails. Remove the worktree, run the check on the real tree, and confirm it passes. Report both outputs. If you cannot make it fail, call it a **weak check** and say so; never present it as protection.
5. Print the TOML block for the user:
   ```toml
   [[claim]]
   id = "C2"
   said = "<the user's exact sentence>"
   to = "<who it was promised to>"
   since = "<YYYY-MM-DD>"
   cosign = ""   # someone who must agree to this claim, for example a domain expert
   ```
   The check is found by id: `claims/checks/<id>.sh` or `.py`. There is no `check` field.
6. After the user pastes it, run `pace.py check` and report the line for the new claim.

## On a continuity break
1. Do not change the claim, the check, or the mode.
2. Find the change that caused it (`git diff`, `git log -p` on the files the check reads).
3. Tell the user in one line: claim id, the sentence, the change that broke it. Then stop.
4. The user decides: revert the change, or change the claim. A changed claim means the promise changes, so the user tells whoever it was made to.

## Check status
`pace.py check` prints one line per claim: `holds`, `BREAK`, `error` (the check could not run or timed out; does not block) or `uncompiled` (no check yet). Report it as it is, in 100 words or fewer.
