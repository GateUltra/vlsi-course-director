# Complete Placement Lesson 06 — delivery evidence

Local delivery, 2026-11-11. No repository push or public deployment was performed.

## Delivered course

- Eight chapters, 39 semantic narration cues.
- Four real narrated H.264/AAC videos, 1920 × 1080 at 30 fps.
- British Thomas: 398.200 s; American Guy: 394.267 s; Indian Prabhat: 463.133 s; Mandarin Yunxi: 415.500 s.
- Seven independently selectable caption languages for each voice: 28 VTT files.
- Three shared-component experiments and six activities, including a practical check that accepts different feasible layouts.
- Scientist with a closed mouth, subtle moustache movement and coordinated hand targets; local feedback based on actual model metrics.
- Website source, original script/translations, voice-specific clocks, source records and a portable local server.

## Numerical and scene evidence

`domain-checks.json` compares five density-weight traces with the archived upstream reference to within 1e-12, independently checking 170 states and the fixed anchors. The reference’s final HPWL is 48.121176 at default weight 0.55; overflow remains 2.

`film-scene-checks.json` covers all 39 scenes, numeric examples, deterministic rendering and caption-safe teaching text placement. `real-clock-checks.json` compares 117 semantic states for each of four measured narration clocks. The same positions and capacity are used by the film and lab.

## Actual final media

`media-checks.json` records complete decoding of all four final MP4s: 11,946 / 11,828 / 13,894 / 12,465 frames. It verifies all 123 actual retimed picture clips against their cumulative integer-frame boundaries, with no accumulated frame discrepancy. Maximum cue-boundary deviation is 30.667 ms, below one 30 fps frame.

Twelve exported-audio windows from the beginning, middle and end match their WAV masters with a minimum zero-offset correlation of 0.999968. All tested timing offsets are zero. Peaks remain below 0.81 and there are no decode errors. These are technical checks, not a claim of human audition.

`audio-checks.json` verifies the 156 exact script/voice/rate caches, actual clip durations, caption bounds, line lengths and decimal-token preservation. The decimal protection covers 48.1, 48.5 and locale comma decimals across sentence, cue and CJK wrapping boundaries. Translated caption fragments use proportional semantic timing; native-language proofreading is not claimed.

## Website and interaction

`site-browser-checks.json` records real-media playback for four voices, 32 chapter jumps, all 28 caption selections, 12 exact video-state transfers, independent subtitle/speed state, rapid voice changes, fullscreen captions, desktop/mobile layout and local-file guidance. The final report contains no JavaScript or HTTP errors.

Webpage captions appear below the picture, keeping diagrams and scores visible on small screens. Fullscreen switches to native captions and returns to the separate caption strip on exit. English, Japanese and Korean screenshots show both desktop and mobile presentation.

`lab-browser-checks.json` additionally checks reference stepping, weight changes, fixed points, keyboard focus, touch-friendly nudges, feedback and activity grading.

## Reopen and package

Run `START_COURSE.cmd` in the project, or extract `Placement_Lesson06_Complete_Website.zip` and run its `START_PREVIEW.cmd`. Open http://127.0.0.1:8770/.

The portable package includes all final media and editable website components; large raw speech and rendering intermediates remain in `production/`. Build scripts remain in `scripts/`. Archive CRC, file count and SHA-256 are recorded separately in `package-check.json` after packaging.
