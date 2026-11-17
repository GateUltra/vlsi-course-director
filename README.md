# VLSI Course Director

Reusable workflows and source for making narrated VLSI/EDA lessons with animated video, interactive experiments and exercises.

## Choose an edition

| Edition | Use it for |
|---|---|
| [HTML Course Studio 2](vlsi-html-course-studio/SKILL.md) | Reproducible HTML/SVG course packs: a shared model, real speech, captions, video export, lab transfer and checks |
| [Original Course Director](vlsi-course-director/SKILL.md) | Lightweight direction with a flexible production technology |
| [HTML Studio v1 archive](downloads/vlsi-html-course-studio-v1.0.0.zip) | The original methods, silent starter and source-only Placement example |

[中文介绍](README.zh-CN.md) · [Reproduction guide](vlsi-html-course-studio/references/reproduce-v2.md) · [Contract](vlsi-html-course-studio/references/course-pack-contract.md) · [Download current skill](downloads/vlsi-html-course-studio-skill.zip)

## What changed in v2

A stable runtime and production CLI now accept replaceable course packs. Domain code, diagrams, cues, narration, subtitles, controls and grading live in the pack. The player, timing, audio assembly, rendering and verification do not know which lesson they are running.

Two small complete benchmarks are included: two-pin wirelength and reconvergent logic timing. Each includes English/Chinese speech fixtures, two subtitle languages, three scenes, an interactive model and a multi-answer exercise. Fixture builds make no TTS calls. These are engineering benchmarks; the preserved Placement example still demonstrates a full 39-cue production and richer character animation.

The contract currently supports deterministic 2D SVG, JSON states, numeric/pointer controls and state-based exercises. It is not an arbitrary-animation compiler. Human review remains necessary for explanation, natural voice, translation and pacing.

## Install and invoke

In a Codex conversation with the built-in installer:

```text
$skill-installer install https://github.com/GateUltra/vlsi-course-director/tree/main/vlsi-html-course-studio
```

Alternatively copy the complete skill folder into your project's `.agents/skills/`. Inspect existing installations before replacing them. The original `vlsi-course-director` name and path remain unchanged.

```text
Use $vlsi-html-course-studio with these course materials: <links or files>.
Create a new course pack, preserving the shared runtime. First deliver a narrated
sample, an exact scene-to-lab transfer and a meaningful exercise.
Validate the model independently and report the executed reproduction checks.
```

For a manual end-to-end reproduction, follow the [isolated environment commands](vlsi-html-course-studio/references/reproduce-v2.md). Raw finished movies and dependencies are not bundled; the small fixed audio inputs are included. A future online synthesis can sound different; the offline fixture path preserves the inputs used to validate the pipeline.

## Evidence and rollback

[Current validation](docs/HTML_STUDIO_V2_VALIDATION.md) records what actually ran and its limits. [Historical v1 validation](docs/HTML_STUDIO_VALIDATION.md) remains separate. Original source and six tools are preserved against a [123-file baseline](vlsi-html-course-studio/references/baseline-v1.json). Reproduction is about repeatable logic and evidence, not identical MP4 bytes across browsers or codecs.

See [migration policy](vlsi-html-course-studio/references/migration-v2.md) before changing shared code. This is a source/skill repository, not a GitHub Pages course website.

## Rights

Original documentation, helpers and new teaching examples are covered by [MIT](LICENSE). Preserve [third-party notices](THIRD_PARTY_NOTICES.md) for the historical course source and character assets. Synthetic fixture provenance is recorded per clip; no voice models, service credentials or human impersonation are included.
