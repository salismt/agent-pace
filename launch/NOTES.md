# agent-pace README compositions

Built three editable HyperFrames projects, with one scene each and local GSAP assets:

- `hero/`: 1200×600, 15 fps, 12 seconds. Storyline A: ticket → parallel terminal evidence → protected outcome → benchmark → ticket.
- `how-it-works/`: 1200×500, 15 fps, 8 seconds. Locked promise and check, travelling commit token, pass first, refusal second, reset.
- `social-card/`: 1280×640, 1 second, static composition. Pitch, install command and paired terminal evidence; 60 px outer margins.

`hero/SPEC.md` was written before implementation. On-screen wording comes from FACTS.md; shortened commands use ellipses. The pitch keeps its exact wording and wraps across multiple physical lines to retain readable type. Red refusal text uses 24 px or bold 22 px to keep the supplied red while meeting contrast requirements.

## Validation

All three final `npx hyperframes check --json` runs passed: `ok: true`, `browserSkipped: false`, zero lint, runtime, layout and contrast errors. Each ran in the foreground with a 45-second timeout. Full results are in each project's `check-result.json`; diagnostic output is in `check-log.txt`.

Only `line_unread` craft warnings remain:

- Hero: 8. Terminal refusals and benchmark copy have short holds under the prescribed beat timings. The final ticket warnings describe the loop reset; its hold continues into the next iteration.
- Mechanism: 1. The exact stop instruction holds about 2.47 seconds, below the check's 3.07-second floor. Kept the specified 8-second pass/fail cycle.
- Social card: 9. The validator treats its 1-second still container as a video with closing lines. The exported still has no reading deadline.

`audio_none` is informational: all three pieces are intentionally silent. No render, snapshot or preview was run. Automated browser audits ran as part of the required check; maintainer frame review remains outstanding. Plan usage was reported as unknown (`usage_request_failed`). The CLI could not persist its global history because that directory is outside the writable workspace; local check results above were saved explicitly.

## Copy omitted or shortened

The brief's selected short ticket note replaces the full original. Commit commands are shortened with ellipses. The hero omits the plain-hook agent's optional final reply fragments. The right-side quoted C1 promise, both refusal bodies, agent reply and outcome stamps remain intact. Other FACTS.md material outside storyline A is omitted: Claude benchmark numbers, the 5-of-24 attempt count, the full README mechanism prose and explanatory ownership sentence. No transcript committer identity, email or personal path appears.

No commit was created. GIF and PNG exports remain for the maintainer, as the brief requires.

## Review 1

Applied the maintainer's review. This section supersedes the initial layout and warning counts above.

- Hero: ticket is 1040×380, centred at (600,300), with 40 px note text and 24 px label. The return uses the identical ticket geometry. Owner-only refusal stays above the commit refusal until the result beat. Its body is shortened to `pace: pace.toml is owner-only.`; the trailing instruction is omitted; the quoted C1 promise stays intact. Panes extend from y=110 to y=560, then contract to y=440 over 8.5–9.0 seconds. Benchmark context now uses the complete requested attribution and caveat.
- Mechanism: two 300×280 cards and a commit gate span the frame. The token travels horizontally from the check to the gate, clears both cards, passes through in green, and stops before the gate in red. Check-card border and text show replay and result states. Failure copy sits under the gate at 22–24 px.
- Text constraint: `replaying…` and `BREAK` do not exist in FACTS.md. Used `…`, `C1 holds`, and `pace: continuity break …` instead, preserving FACTS.md as the only source of on-screen wording.
- Social card: both mini panes now use content height plus padding. The pair remains vertically centred against the pitch.

All three final foreground `npx hyperframes check --json` commands exited 0 within their 45-second timeouts. All report `ok: true`, `browserSkipped: false`, and zero lint, runtime, layout and contrast errors. Contrast checks covered visible text in all three projects. Results and logs replace each project's previous check files.

Remaining warnings: hero 6 `line_unread` warnings for the prescribed short refusal/benchmark beats and loop return; mechanism 0; social card 9 `line_unread` warnings because its still container lasts one second. These preserve the requested timings and still-image format. No render, snapshot, preview or commit was made.
