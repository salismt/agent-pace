# Review 1 (maintainer, from snapshots)

Checks pass. Fix these, keep everything else. Same rules as BRIEF.md (FACTS.md text only, no render/snapshot, foreground checks).

## hero/
1. Frame 0 is the GIF thumbnail and is too small: the ticket card fills only ~45% of the frame. Make the card ~1040 px wide, vertically centred, note text 40 px (label 24 px). Same for the loop-back state at 11.2–12.0 so the loop still matches frame 0.
2. The owner-only refusal (`✎ pace.toml` → `pace: pace.toml is owner-only. …`) is on screen only 2.6–3.9 s, then the commit refusal replaces it in the same place. Keep it visible: show it first, then print the commit refusal BELOW it in the same pane. To fit, shorten the owner-only line to `pace: pace.toml is owner-only.` and drop the `Do not edit the claim or its check…` line (FACTS allows shortening with "…"; keep the quoted C1 promise intact).
3. From 2.6 s to 9.0 s the bottom ~40% of the frame is empty. Make both panes tall (top ~110 px to bottom ~560 px) while they print; at 9.0 s, before the number lands, shrink the panes upward to free the bottom band for the number line.
4. Number line: say whose numbers they are: `Codex GPT-6.1-Sol · PromiseBench override tickets · all breaks came from 2 of 6 projects` (replace the "PromiseBench …" ellipsis line).

## how-it-works/
1. The diagram uses the left 45% of the frame and the type is small. Lay it out as one clean left-to-right row filling ~1100 px: `pace.toml` card → `claims/checks/C1.py` card → a gate labelled `commit`. Cards ~300 px wide, text ≥ 22 px, mono ≥ 20 px.
2. The `git commit` token currently overlaps the check card's bottom edge and the connector takes a detour below the card. Run the token along one straight horizontal line between the cards, above nothing, never overlapping a card.
3. Replace the loose spinner glyph with a clear state change on the check card itself: border and a small label `replaying…` then `holds` (green) or `BREAK` (red). The pass branch ends with the token through the gate in green; the fail branch stops the token at the gate in red and shows the two message lines under the gate, not under the check card.
4. Use the empty lower band: the failure message lines sit there, 22–24 px.

## social-card/
1. The two mini panes are half empty at the bottom. Shrink their height to the content plus padding, and centre the pane pair vertically against the text block. Everything else is good.

When done: run `npx hyperframes check --json` in all three, update NOTES.md with a "Review 1" section, stop.
