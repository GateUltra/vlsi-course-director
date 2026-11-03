# Learning website and delivery

## Learning experience

Connect the requested video to concise context, lesson objectives, an interactive demonstration, prediction/experimentation and meaningful feedback. The interaction should share verified course data with the narration and visualizations where appropriate. Show invalid inputs and explain their first failing rule; don't reject valid alternatives simply because they differ from a single reference answer. Separate structural validity, completeness and physical or domain constraints when the course requires it.

Use responsive layout, readable contrast and native controls/accessibility semantics. Chapters should appear alongside the player on wide screens and remain accessible on mobile. Support chapter seeking, playback speed, audio choice and independent subtitles; preserve current position and play/pause state when practicable.

## Optional media contract

For a static website with separate video files per narration, one workable contract is:

```json
{"tracks":[{"id":"en_gb","label":"British English","video":"media/lesson-en_gb.mp4","captions":{"en":"media/captions/en_gb-en.vtt"}}]}
```

Place that in `media/manifest.json` and put measured timelines in `data/timings.json` under `languages[trackId]`, with `duration` and ordered `scenes[]`; scenes include stable `id`, `start`, `end`, and `cues[]` with `id`, `start` and `end`. Names and counts should reflect the new lesson rather than a prior project. Store paths relative to the site root and resolve them relative to the current deployment base path.

For chapter jumps, use the selected voice's scene start. When changing voices, map the current scene and cue ID plus proportional progress to the corresponding cue in the new timeline, rather than reusing elapsed seconds. Handle unavailable files and tracks gracefully; allow an independent caption selection to persist if supported.

`python scripts/validate_site_media.py PATH_TO_SITE` checks this particular contract, timing/caption bounds and the existence and basic audio/video streams via `ffprobe`. It does not prove technical correctness of a lesson, translation quality, or subjective audio/visual synchronization. Adapt or replace it for another site architecture.

## Preview and verify

Direct `file://` access can prevent manifest, timeline and subtitle requests. Serve the site via HTTP locally, provide a clear startup instruction, and support byte ranges so video seeking works. The bundled `scripts/serve_site.py --directory PATH_TO_SITE --port 8765` binds localhost and supports Range; it is a preview server, not a production server. If appropriate, provide a platform-friendly startup shortcut with an explanation when a port is occupied.

Use real browser tests for actual video loading, seeking every chapter, cue-preserving voice switching, playback speed, selected subtitle `showing` state and loaded cues, turning captions off, keyboard usage, lab interactions, errors, mobile width and page overflow. Test with the final real files, not only mocked metadata. Preserve reproducible test evidence and distinguish tool-level verification from human evaluation.

## Publish only when requested and authorized

Before publication, confirm the actual destination and integration plan. A new standalone static GitHub Pages project can publish files from `main` and `/(root)` or `/docs`; an established course repository may have its own site structure and workflows and must not be replaced wholesale. Preserve relative paths and the entry point, and research current platform constraints. Static hosted pages do not need the localhost Python server.

Verify the deployment workflow result and actual remote HTTP responses for page, manifest, timed captions and byte-range video, plus real browser playback when available. A configuration response or a `building` status is not evidence of a live site. Do not say published if there is no actual evidence. Report residual human-review needs and deliver editable source, media, attribution, tests and usage instructions.
