# VLSI Course Director

[中文说明](README.zh-CN.md) · [Detailed HTML studio guide](docs/HTML_STUDIO_GUIDE.md) · [Download the new skill](downloads/vlsi-html-course-studio-skill.zip)

Reusable community skills for making VLSI / EDA lessons: instructional planning, animated teaching video, narration, independent subtitles, interactive experiments, exercises, and editable sources. These are project-derived agent skills, not official OpenAI skills or a hosted course website.

## Choose a skill

| Skill | Best fit | What is included |
|---|---|---|
| **[vlsi-html-course-studio](vlsi-html-course-studio/SKILL.md)** — new | Shared HTML/SVG animation for video, a live lab, and exercises; multilingual production and an interactive teaching character | 9 detailed guides, 6 portable tools, a runnable silent starter, and a source-only Placement Lesson 06 example |
| **[vlsi-course-director](vlsi-course-director/SKILL.md)** — original, retained | A lighter, technology-flexible workflow for course research, direction, video/audio and website delivery | Original instructions, lesson blueprint, Floorplanning case study, preview server and media validator |

The original skill folder and its installation path are unchanged. The new skill has a distinct name; you can keep both and explicitly select the one appropriate to a task. The new skill's detailed guides are in Chinese; code and example teaching interfaces are in English. This README and the [usage guide](docs/HTML_STUDIO_GUIDE.md) provide English entry points.

## Install and invoke

In Codex with the bundled skill installer, send this as a **chat prompt**, not a shell command:

```text
$skill-installer install https://github.com/GateUltra/vlsi-course-director/tree/main/vlsi-html-course-studio
```

For the original skill, use:

```text
$skill-installer install https://github.com/GateUltra/vlsi-course-director/tree/main/vlsi-course-director
```

For manual project-local installation, clone or download this repository and copy the complete selected skill folder to `.agents/skills/` inside your project. Keep `SKILL.md`, `agents/`, `references/`, `scripts/` and `assets/` together. Check an existing installation before replacing it. Codex discovers local skills; if a newly installed skill does not appear, restart the session. See the [official skill documentation](https://learn.chatgpt.com/docs/build-skills).

Then provide the actual lesson materials and intended scope:

```text
Use $vlsi-html-course-studio for this VLSI lesson: <course URL>.
The audience is university students learning the topic for the first time.
Create a 45–60 second narrated sample and an interactive version that shares
the same diagram and state. Explain the model, test a prediction, and include
one exercise. Use the voice and visual direction we have agreed on.
```

Other agents can read the chosen `SKILL.md` directly or install it using their supported skill mechanism. A request for planning only remains a planning task; the skill does not automatically authorize online speech services or publication.

## Try the new starter without generating speech

Run from the repository root with Python 3.10+:

```powershell
python vlsi-html-course-studio/scripts/init_course.py --destination ../my-vlsi-lesson --title "My VLSI Studio"
python vlsi-html-course-studio/scripts/serve_site.py --directory ../my-vlsi-lesson --port 8780
```

Open **http://127.0.0.1:8780/**. The destination must be a new directory. This original two-pin example is a **32-second silent storyboard**, explicitly marked as provisional. It demonstrates a shared SVG board, exact scene transfer into a draggable/keyboard-accessible lab, metric-based companion comments, and an exercise accepting multiple solutions. It does not contain a generated narrated movie or call an online service.

Optional model checks:

```powershell
node ../my-vlsi-lesson/check.mjs
```

For real video production, install the needed Playwright/Chromium and FFmpeg dependencies, create authorized narration and measured cue clocks, then follow the [production guide](docs/HTML_STUDIO_GUIDE.md). Viewing a finished static lesson does not require the production tools.

## New skill contents

```text
vlsi-html-course-studio/
├── SKILL.md
├── agents/openai.yaml
├── references/                      Nine focused production guides
├── scripts/                         Init, preview, render, retime and validation
└── assets/
    ├── planning/                    Lesson brief and cue template
    ├── starter/                     Runnable original silent example
    └── placement-lesson06-source/    Worked source snapshot, no final movies
```

The worked example includes the closed-mouth scientist rig, two-bone arm IK, local lab feedback, voice-specific timing, caption handling and the original production scripts. Its historical course scripts retain course-specific settings; the portable tools are in the top-level skill `scripts/` folder. Read [SNAPSHOT_README.md](vlsi-html-course-studio/assets/placement-lesson06-source/SNAPSHOT_README.md) before trying to rebuild it.

The [validation record](docs/HTML_STUDIO_VALIDATION.md) distinguishes executed tool/browser checks from human listening and translation review. The small downloadable package excludes finished MP4s, raw audio, installed dependencies and private working directories.

## Credit and license

Original skill instructions, portable helpers and original starter code are available under the repository's [MIT License](LICENSE). Third-party artwork and source-derived examples retain their separate provenance; the repository license does not grant rights to third-party material. See [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md) and the worked example's [CREDITS.md](vlsi-html-course-studio/assets/placement-lesson06-source/course/CREDITS.md).

The course examples credit Yongfu Li and the [EDA Learning project](https://github.com/yongfu-li/eda-learning). The new example explicitly records that the upstream course's stated license intention was not verified as a license grant. Preserve those distinctions when adapting or redistributing examples.
