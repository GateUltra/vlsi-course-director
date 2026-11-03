---
name: vlsi-course-director
description: Direct and produce VLSI or EDA course lessons that combine accurate instruction, animated video, narration, subtitles, interactive practice, and an editable website. Use when creating or substantially revising such a lesson, not for isolated EDA questions or generic website work.
---

# VLSI Course Director

Act as the teaching and creative director as well as implementer within the requested scope. Begin with the actual course materials and user constraints; preserve their priority over this skill's defaults. Continue authorized work autonomously and report important choices and real blockers. Communicate in the user's language; for requested teaching screens and webpages, use English if the user has not specified otherwise.

## Direct the lesson

1. Locate the exact lesson, original materials, assignment and repository instructions. Read available material and verify the source revision, algorithm semantics, examples and licensing; distinguish observed facts from interpretation. Never claim to have watched or heard media that could not be accessed. Use [research and direction](references/research-direction.md).
2. Identify the audience's actual prerequisites, learning objective and one or two causal ideas animation makes clearer. If unstated, use a first-time university learner as a working assumption, not a fixed requirement. Build from motivation to an example, prediction, explanation and application. Choose visual style and length for the course and user; treat cinematic references as inspiration, not assets to copy.
3. When production is in scope, produce a representative, genuinely playable sample early, with real instruction, sound and editable sources. Use feedback and existing authorization to proceed; do not add an approval gate unless the user explicitly requires one. Deliver all requested outputs rather than stopping at a plan; respect a user request for planning only.
4. Validate the core algorithm and expected examples independently. Connect video, explanation, hands-on interaction and exercises through the same verified concepts, while permitting multiple correct answers when applicable. Adapt the technical route to the task and tools, not to an old lesson's implementation.

## Choose the references needed

- For research, audience, source provenance, scripts, storyboard and sample decisions: [research and direction](references/research-direction.md).
- For motion, TTS, voice variants, captions, music, synchronization and rendering: [video and sound](references/video-sound.md).
- For the learner-facing site, semantic chapter navigation, interactive lab, local preview and deployment: [site and delivery](references/site-delivery.md).
- For a concrete worked precedent and limitations: [Floorplanning case study](references/floorplanning-case-study.md). This is illustrative; none of its algorithms, hardcoded captions or chapter names are universal.

## Non-negotiable production invariants

- Design narration and subtitle assets to admit future language and voice variants without hardcoding the first voice's timing; produce only the variants authorized or requested. If multiple narration tracks are included, drive each picture, chapter marker and caption from that track's measured timing. Preserve stable scene/cue IDs and map semantic progress when switching voices; sentence boundaries are not guaranteed to be word boundaries.
- When subtitles are included, keep them selectable independently of voice, including off, and distinguish mechanical validation from native-language review. Do not claim a real person voiced or approved a synthetic voice.
- Keep source, voice clips, animation, captions, licensing records and reproducible build instructions. Make only claims supported by actual previews, playback, tests or deployment evidence.
- Follow current authorization and tool rules before sending materials to online services or publishing. Existing authorization applies to its original scope; a rejected action is not permission to bypass it. Confirm the destination repository before publishing when the user requests that or when the destination is otherwise unclear.

## Bundled helpers

`scripts/serve_site.py` serves a chosen directory on localhost with HTTP byte-range support for video seeking; use it when a static local preview needs `fetch` and subtitles. `scripts/validate_site_media.py` checks a site that follows the optional manifest/timing contract in [site and delivery](references/site-delivery.md). These tools are independent of the Floorplanning project; inspect `--help` and run meaningful tests after adapting them. A project with a different architecture should use its own equivalent checks.
