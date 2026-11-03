# VLSI Course Director

A reusable AI agent skill for creating VLSI and EDA lessons that combine accurate technical explanations, animated teaching video, narration, independent subtitles, an interactive learning site, and editable production sources.

This is a community skill derived from a teaching project, not an official OpenAI skill. It helps an agent research the specific lesson, choose an instructional narrative, create an early representative sample when production is requested, and verify the finished experience. It does not prescribe one particular EDA algorithm or visual style.

## Use in Codex

Ask Codex to install the skill from this repository with its skill installer:

```text
$skill-installer install https://github.com/GateUltra/vlsi-course-director/tree/main/vlsi-course-director
```

Alternatively, clone this repository and copy the complete `vlsi-course-director/` folder into your agent's skills directory. For a project-local Codex skill, that can be `.agents/skills/vlsi-course-director/` inside the project. Make sure `SKILL.md`, `references/`, `assets/`, and `scripts/` remain together. Follow the current instructions of your agent environment for discovering newly installed skills; restarting the session may be necessary.

Then provide the new lesson's actual course material and instructions. For example:

```text
Use $vlsi-course-director to develop this EDA lesson from the attached course materials.
First identify its learning goals and produce a representative sample.
```

The skill respects the requested scope: if you ask only for a plan, it should not produce or publish unrequested media. You remain in control of online services and publication.

## What's included

```text
vlsi-course-director/
├── SKILL.md                 Agent instructions and routing
├── agents/openai.yaml       Codex interface metadata
├── assets/                 Reusable lesson blueprint
├── references/             Direction, media, site and case-study guidance
└── scripts/                Local preview and optional media validation
```

The optional helpers use Python 3.9 or newer. The media validator also needs `ffprobe` from FFmpeg on `PATH` and checks the example manifest contract described in the skill; it is not a universal validator for every possible site.

```bash
python vlsi-course-director/scripts/serve_site.py --directory /path/to/site --port 8765
python vlsi-course-director/scripts/validate_site_media.py /path/to/site
```

The preview server listens on `127.0.0.1`; it supports byte-range requests for video seeking. Neither tool substitutes for instructional review, real listening, translation review, or browser testing.

## Credit and license

The skill's original files are available under the [MIT License](LICENSE). The case study credits the [EDA Learning Floorplanning course](https://github.com/yongfu-li/eda-learning/tree/main/courses/learn_floorplanning) by Yongfu Li and contributors, whose original course materials are identified as [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). Linked third-party materials retain their own licenses; no course videos, narration, music, or third-party source files are bundled here.
