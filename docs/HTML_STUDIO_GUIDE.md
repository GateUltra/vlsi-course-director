# Using VLSI HTML Course Studio

This guide is an English entry point to the new skill. Its nine detailed references are written in Chinese; agents can read them directly. The full skill lives in [`vlsi-html-course-studio/`](../vlsi-html-course-studio/SKILL.md). The original [`vlsi-course-director`](../vlsi-course-director/SKILL.md) remains available separately.

## Start with your lesson

Give the agent the real course/assignment URLs or files, intended audience, deliverables, visual/voice preferences and any existing authorization for online services. Request a plan, a representative sample or a complete course explicitly. The skill does not inherit the sample project's speech-service or publishing authorization.

For a new lesson, a useful first production request is a 45–60 second narrated sample containing one real concept, a causal animation, a prediction, exact scene transfer into a lab, and a meaningful exercise. A title sequence alone does not test the teaching or synchronization.

## Understand the shared design

```text
verified domain model → shared diagram component
script + measured voice clock → deterministic scene state → HTML/SVG → MP4
                                             ↓
                                   exact snapshot → lab → feedback + exercises
```

Stable cue IDs connect narration, captions, chapters and lab entry points. Each voice has a measured clock. Voice switching preserves the cue and normalized progress rather than the same elapsed seconds. The companion computes its feedback from actual metrics; exercises assess constraints and allow different correct solutions.

## Run the silent starter

From the repository root:

```powershell
python vlsi-html-course-studio/scripts/init_course.py --destination ../my-vlsi-lesson --title "My VLSI Studio"
python vlsi-html-course-studio/scripts/serve_site.py --directory ../my-vlsi-lesson --port 8780
```

Open http://127.0.0.1:8780/. Keep the server running. The generator refuses an existing destination. This is a 32-second silent storyboard with a provisional clock, not a narrated course. It makes no online TTS calls.

In a second terminal, run the model checks:

```powershell
node ../my-vlsi-lesson/check.mjs
```

For optional real-browser tests, install Python Playwright and its Chromium in your chosen environment, then run:

```powershell
python -m pip install playwright
python -m playwright install chromium
python ../my-vlsi-lesson/check_browser.py
```

You can instead point `--browser` to an existing local Chromium executable. Dependencies are not bundled; viewing the starter only needs the local server and browser.

## Render and adapt

With the starter server running, inspect representative frames:

```powershell
python vlsi-html-course-studio/scripts/render_html.py --url http://127.0.0.1:8780/render.html --clock ../my-vlsi-lesson/content/demo-clock.json --preview-dir ../my-vlsi-lesson-review
```

The page exposes `window.ready`, `window.clock` and `window.renderAt(t)`. The renderer checks the exposed clock and calls the deterministic scene at each frame. A preview directory is useful before spending time on a full movie. To export a silent MP4, use `--output` instead of or alongside `--preview-dir`; FFmpeg must be available. The demo clock remains provisional until replaced by measured narration data.

For real production:

1. Replace the two-pin domain and test fixtures with the new lesson's verified model.
2. Author semantic cues and visual beats, including definitions and counterexamples.
3. Generate authorized voice clips, cache exact text/voice/settings and measure durations.
4. Drive diagrams and annotations from the actual cue clocks. For compatible normalized animations, `retime_video.py` can match one silent picture master to another voice's semantic windows without speeding up speech.
5. Generate caption files for each requested voice/language combination, independent of voice selection.
6. Integrate a player, exact lab transfer, metric-based feedback and objective-aligned exercises.
7. Validate real media, caption layout, chapters, rapid voice switches, keyboard/touch interactions and archive reopening.

Reference commands and limits are in [tooling](../vlsi-html-course-studio/references/tooling.md), [audio/captions](../vlsi-html-course-studio/references/audio-captions.md) and [site verification](../vlsi-html-course-studio/references/site-verification.md). New scripts use Python 3.10+; rendering uses Playwright/Chromium and FFmpeg/ffprobe. The original worked-example audio generator also uses `edge_tts` and NumPy and requires configuration before calling a speech service.

## Use the worked example as source

[`assets/placement-lesson06-source/`](../vlsi-html-course-studio/assets/placement-lesson06-source/SNAPSHOT_README.md) contains the actual full-course components and historical evidence: closed-mouth scientist, two-bone IK, 39 cues, four voice clocks, 28 VTT files, three labs, exercises, the player and production scripts.

It omits finished movies, raw speech/audio masters, picture masters and installed dependencies. Its `course/README.md` describes the original complete project, not a turnkey website inside this skill. Course-specific scripts retain historical browser/port settings. Use the portable top-level tools for new work, and preserve source/asset provenance.

## Validate the tools

```powershell
python vlsi-html-course-studio/scripts/check_tooling.py
python vlsi-html-course-studio/scripts/check_tooling.py --integration
```

The integration check renders a tiny deterministic scene, retimes semantic segments, muxes a test audio track and decodes the result. It also rejects mismatched clocks and truncated streams. It does not replace instructional review, real listening, native-language review or the actual course's browser checks. See [executed validation](HTML_STUDIO_VALIDATION.md).
