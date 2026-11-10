GOAL: Show how an override ticket breaks a promise under a plain hook and is refused by agent-pace.
OUTPUT: HyperFrames, 1200 x 600, 15 fps, silent GIF source.
TIME: 12 seconds x 15 fps = 180 frames. No music.
LOOK: #F6F4EE ground, #1F1E1C ink, #6B6A65 muted; terminals #1C1B19 / #E8E6DC. Red #E24B4A means broken/refused; green #1D9E75 means committed. Inter 600, 40 px titles; IBM Plex Mono 22 px terminal lines, 27 px leading. Note 40 px; label 24 px. No shadow, grain, gradient or vignette.
OBJECTS: One 1040 x 380 ticket sheet, centred at (600,300), splits into two 528 x 450 terminal panes at y=110. At 6.4 s the left becomes 312 px and the right 744 px. Terminal content is sourced solely from FACTS.md; the mechanism is an illustration, not invented product UI.
MOTION: Container transforms take 0.6 s power2.inOut; whole terminal lines appear with discrete timeline sets. Highlight scaleX sweep takes 0.4 s. Return completes at 11.8 s, holding three frames matching frame zero. No CSS animation or runtime clock.
SHOTS:
0-29: Ticket visible at frame zero; red 25% highlight begins frame 12.
30-38: Ticket halves become terminal surfaces. Content is exchanged during the split.
39-95: Real terminal lines print in parallel; owner refusal first, then commit refusal. Owner refusal stays above the commit refusal; the trailing instruction is omitted. Quoted promise remains intact.
96-134: Left pane contracts, right grows; exact agent reply and both outcome stamps hold.
128-134: Panes contract from 450 to 330 px tall to free the benchmark band.
135-167: Counts land with the required caveat. Setup remains visible above panes.
168-179: Pane surfaces fold back to the note. At frame 177 the initial state is restored.
BANNED: Dark void, glow, particles, gradients, 3D tilt, floating or breathing objects, slide-up fades, three cards in a row, corner logo, prompt typing opener, invented claims, transcript identity/path metadata.
QA: Maintainer should inspect frames 0,12,30,38,65,95,104,135,167,177,179. This task explicitly forbids render, snapshot and preview. Run check in foreground with timeout; report browser limitations instead of claiming visual verification.
