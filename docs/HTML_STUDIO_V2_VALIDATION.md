# HTML Course Studio 2.0.0 — executed validation

Validation date: **2026-11-17**. This report concerns the new shared runtime and its two small narrated course packs. It does not substitute historical Placement results for v2 evidence.

**Local acceptance passed.** Both packs were rendered from source, fully decoded and exercised in real browsers. A separate agent authored the second domain from the public contract and independently rebuilt it without changing the engine. Machine-readable results, source hashes and browser observations are in [studio-v2-evidence.json](studio-v2-evidence.json).

## What can now be reproduced

The stable runtime and production CLI accept a course pack containing a model, SVG drawing code, semantic cues, narration, translated captions, controls, feedback, grading and independent mathematics tests. The same adapter produces the film frames and the interactive lab. Importing a scene transfers its exact intermediate JSON state rather than reconstructing a similar preset.

Follow the [isolated reproduction commands](../vlsi-html-course-studio/references/reproduce-v2.md). The repository includes twelve fixed speech clips, with text/settings/file hashes and provider provenance. Fixture mode needs no online speech service; it generates actual MP4/WebM video, VTT captions and a portable static website. Python, Node, FFmpeg and the browser are declared external dependencies.

| Benchmark | Model | Tested output per voice | Voices / caption languages |
|---|---|---|---|
| `wirelength` | Two-pin bounding-box width + height; movable endpoint | 1280 × 720, 30 fps; EN 696 frames, ZH 672 frames | British English + Chinese / EN + ZH |
| `logic-timing` | Reconvergent paths; max arrival + final gate delay | 1280 × 720, 30 fps; EN 823 frames, ZH 848 frames | British English + Chinese / EN + ZH |

These are approximately 22–28-second engineering benchmarks. They are deliberately small enough to rebuild and diagnose. A full lesson still needs source research, direction, pacing and human review.

## Executed environment and checks

The clean Windows environment used Python 3.11.4, Node 24.22.1, Playwright 1.56.0, edge-tts 7.3.1 and FFmpeg's 2025-04-21 build. The full tested Python dependency lock is included. A fresh isolated Playwright browser download was used, not an earlier course's hidden dependencies.

| Check | Executed result |
|---|---|
| Course admission and independent model tests | Both packs passed; unknown versions/scenes, duplicate cues and missing translations are rejected |
| Adapter and shared-core checks | Both passed; serializable states, deterministic random access, stable controls and exact snapshot transfer |
| Full production | Both packs, two voices each; MP4 H.264/AAC and WebM VP8/Opus; complete EN/ZH captions |
| Cross-artifact verification | Source, audio and output hashes; cue order and caption text; measured voice clocks; video frames and decoded audio samples; complete media decode |
| Failure regression | **25 checks per pack**, including stale audio/text, missing/extra cues, truncated video/audio, altered source/output and stale but syntactically valid subtitles |
| Real browser matrix | **6/6 passed**: both packs in Playwright headless shell 141, full Chromium 141 and Chrome 156 |
| Independent migration and rebuild | New logic-timing domain, public contract only; **zero engine changes**; a separate source build with no reused movies or online TTS |
| Historical preservation | **123 protected files unchanged**, including original director, v1 starter, Placement source and six legacy tools |

Each browser run checked both advancing, unmuted voice tracks and decoded audio signal; four voice/caption combinations; six chapter jumps and six exact intermediate scene transfers; semantic and rapid voice switching; speed/pause preservation; controls, feedback, reset and multiple correct exercise answers. It also checked native fullscreen, a 390-pixel mobile viewport, incompatible snapshot rejection and an explicitly unsupported-media case. There were no unexpected page, HTTP or external-request errors in the final six runs. Numeric interaction is required; pointer interaction is additionally tested where the pack supplies it.

The open-source Chromium variants actually played VP8/Opus; Chrome played H.264/AAC. This distinction matters: a browser capable of rendering animation frames is not necessarily able to decode the finished MP4.

## Independent migration evidence

A separate agent received the public course-pack contract, without reading the wirelength pack or runtime implementation. It implemented a different state space—three gate delays, reconvergent maximum arrival and a critical-path exercise—and independent expected-value tests. The final reproduction followed the documented commands using a copied skill and copied pack. All 21 copied runtime/production files and 11 pack files remained unchanged during that build.

The independent build produced the same source/audio/render identity as the release candidate:

```text
wirelength:   509c0a894be2c70bf61ca3e98a2046ec398ed44b642b07afd0241ccf63e95c7d
logic-timing: e7a30a82d3633e1b9c61a495b27aaf43bb3067dfe79c798490fcdf4d2dd1e727
```

These identities do not assert identical encoded movie bytes across machines. The independent agent used the prepared fresh Python/browser installation and needed the managed desktop's ordinary browser/server execution escalation; it did not need unpublished production instructions or a special browser flag. Its complete structured evidence is embedded in the linked JSON.

## Defects found before acceptance

The checks found and drove fixes for Windows serving `.mjs` with the wrong MIME type; proprietary-codec absence in fresh Chromium; a real VP9 decoder failure on the tested Windows browser; lost SVG typography during frame composition; and fullscreen captions covering the principal formula. The final server has explicit MIME handling, the output includes tested VP8/Opus alternatives, adapter attributes are retained, and the main composition reserves more caption space. The final builds and browser checks were repeated after those fixes.

## Public automation and rollback

[The CI workflow](https://github.com/GateUltra/vlsi-course-director/blob/main/.github/workflows/studio-v2.yml) rebuilds both packs from fixed inputs at 640 × 360 / 15 fps on a fresh Linux runner, then performs full media verification, real browser acceptance and failure regressions. Its live status and downloadable evidence are available in [GitHub Actions](https://github.com/GateUltra/vlsi-course-director/actions/workflows/studio-v2.yml). Local Windows success and a future hosted run are separate claims; consult the actual run for Linux evidence.

The [v1 archive](https://github.com/GateUltra/vlsi-course-director/blob/main/downloads/vlsi-html-course-studio-v1.0.0.zip), [historical report](https://github.com/GateUltra/vlsi-course-director/blob/main/docs/HTML_STUDIO_VALIDATION.md) and [baseline hashes](../vlsi-html-course-studio/references/baseline-v1.json) remain available. The [migration policy](../vlsi-html-course-studio/references/migration-v2.md) separates course-pack changes from versioned contract/engine evolution.

## Limits of this release

- Supported migration is deterministic 2D SVG with JSON state, numeric or pointer controls and state-based exercises. Arbitrary 3D, new interaction types and new speech providers can require a reviewed contract extension.
- The full 39-cue Placement implementation is preserved as a source reference; it has not been wholly ported or proven visually equivalent under v2.
- Fixed-input reproduction is tested. Future online synthesis depends on service access and voice availability; waveform identity is not promised.
- Decoded audio signal and complete subtitle text do not certify natural delivery or translation quality. Native-language review and subjective listening are outside this automated acceptance.
- Representative frames show the main formula clear of native fullscreen captions. The secondary bottom intent strip can still overlap them; browser caption preferences vary. Small internal diagram labels are not all independently readable on mobile, where separate HTML metrics and controls provide the essential values.
- Browser/encoder/font versions can affect appearance and compressed bytes. Logical outputs, source identity, media coverage and contract behavior are the reproducibility target.
