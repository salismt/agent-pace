# Brief for Codex: agent-pace README motion graphics (HyperFrames)

You are building three short, silent pieces for the agent-pace README. No launch film, no voice, no music: the outputs are GIF loops and one still image. Budget matters: keep the compositions simple and finish in one pass.

## Read first (in this order)

1. `~/.agents/skills/hyperframes/SKILL.md` and the references it points to for this job: `references/format.md`, `references/motion.md`, `references/spec.md`, `references/types/launch.md` (the "Real UI, never a mockup" and "Tells" parts). Follow its contract exactly.
2. `FACTS.md` in this folder: the ONLY text allowed on screen. Copy strings verbatim; shorten with "…" only.
3. `STORYLINES.md` in this folder: storyline A was picked.

The projects are already initialised: `hero/`, `how-it-works/`, `social-card/`. Edit their `index.html` (and add `compositions/` scenes if the skill asks for them). Set each root's size as below (edit `data-width`, `data-height`, the viewport meta and CSS). Write `SPEC.md` in `hero/` before building it, per `references/spec.md`.

## Shared look

- Ground: warm off-white `#F6F4EE`; ink `#1F1E1C`; muted `#6B6A65`. Terminal panes: `#1C1B19` with text `#E8E6DC`.
- Colour carries meaning only: red `#E24B4A` = a promise broke or pace refused; green `#1D9E75` = a commit went through. No other accents.
- Type: a bundled sans for titles and a bundled monospace for terminal text (see `references/format.md` for the bundled names). Titles weight 600, max 6 words a line.
- Readability: these are shown in a GitHub README at about 880 px wide. At 1200 px source width, no text below 22 px; terminal text 22–24 px; titles 40–56 px.
- Banned: dark void with floating cards, glow, particles, gradients, 3D tilt, everything sliding up and fading, three cards in a row, a logo docked in a corner, typing into an empty prompt box as the opener.
- Motion: terminal lines appear line by line as a real terminal prints them (a line appears whole, or types at ~40 chars/s for commands only). Panes move as whole objects (split, shrink, grow) with 0.4–0.6 s eases. Every element holds still once it lands.

## 1. `hero/` — the teammate's note (storyline A). 1200×600, 15 fps, 12.0 s, seamless loop

Beats (seconds):
- **0.0–2.0** Frame 0 is already the ticket card, centred, large, on the off-white ground: label `api-stability · override ticket`, then the short-form note from FACTS.md. At 0.8 s a highlighter sweep (red at ~25% opacity behind the text) marks `update the check or skip it`.
- **2.0–2.6** The ticket card splits into two terminal panes side by side (object-to-object: the card becomes the panes). Pane headers: left `plain pre-commit hook`, right `agent-pace`; one shared line above both: `Codex CLI · GPT-6.1-Sol · same ticket`.
- **2.6–6.4** Both panes print their real lines in parallel (FACTS.md "Left" items 1–4 and "Right" items 1–2). Left ends with the commit landing: `[main 846a536]` in green. Right shows each pace refusal in red as it happens. Long lines may be shortened with "…"; keep the quoted promise text intact.
- **6.4–9.0** The left pane shrinks to about one third width and gets the stamp `committed · promise broken` (red). The right pane grows and shows the agent's reply from FACTS.md (verbatim) with the stamp `not committed · promise kept`.
- **9.0–11.2** The number lands across the bottom third: `Plain hook 6/24 broke · agent-pace 0/24`, with the small line `Codex GPT-6.1-Sol on PromiseBench override tickets · all breaks came from 2 of 6 projects`.
- **11.2–12.0** Everything folds back into the ticket card so the last frame matches frame 0 (the GIF loops without a jump).

## 2. `how-it-works/` — illustration of the mechanism. 1200×500, 15 fps, 8.0 s, seamless loop

One frame that rebuilds (no cuts). Left to right: a `pace.toml` file card showing the example promise `C1: "Fields in /v1 responses are never removed or renamed." (to API customers)` with a small lock and the label `owner-only` → an arrow into `claims/checks/C1.py` (also locked) → an agent commit token `git commit` travelling along the line → the check replays → branch A: check passes, the token turns green and goes through `commit`; branch B (second half of the loop): check fails, the token stops in red and a message card shows `pace: continuity break …` and `Tell the user in one line which change caused it, then stop.` Show pass first (0–3.5 s), then fail (3.5–7.4 s), then reset to frame 0 (7.4–8.0 s). Labels only from FACTS.md "Product copy".

## 3. `social-card/` — repo social preview. 1280×640, a still

A single composition, 1 s long, designed as a still (the last frame is the image). Left 55%: the pitch from FACTS.md as the title (two lines: `Let your agents run.` / `Get interrupted only when they break a promise you made.`), the wordmark `agent-pace` above it, the install command in a small monospace pill below. Right 45%: a static miniature of the hero's split moment: left mini-pane with `[main 846a536]` green and stamp `promise broken`, right mini-pane with `pace: pace.toml is owner-only.` red and stamp `promise kept`. Keep 40 px safe margins (GitHub crops social images).

## Done means

- In each project: `npx hyperframes check --json` reports no errors (fix every error; weigh warnings).
- Write a short `NOTES.md` in `launch/` listing what you built, any check warnings you left and why, and anything in FACTS.md you could not fit.
- Do NOT render, snapshot or preview: those need a browser that your sandbox blocks. The maintainer will run them and send you frame feedback.
- Do not edit anything outside `launch/`. Do not commit.
- Run every check in the foreground with a timeout, read its output, fix, repeat.
