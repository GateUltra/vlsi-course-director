# The Placement Studio — Lesson 06

A complete local teaching website: eight video chapters, four narration tracks, seven independently selectable caption languages, three interactive experiments and six practice activities. Screens and notes are in English; narration includes Mandarin.

## Open the lesson

On Windows with Python installed, double-click **START_PREVIEW.cmd** in this folder, keep the terminal open, and visit **http://127.0.0.1:8770/**. Alternatively:

```powershell
python serve_site.py --directory . --port 8770
```

Opening `index.html` directly with `file://` prevents the data and subtitles from loading correctly. If port 8770 is already occupied by this lesson, use the existing server. Otherwise choose another port in the command and URL.

The website is static and uses relative file paths. It can later be hosted from a GitHub Pages repository or subdirectory without the Python server. This delivery has **not been published**.

## Watch, transfer and experiment

- Choose British English (Thomas), American English (Guy), Indian English (Prabhat), or Mandarin (Yunxi). They are synthetic service voices.
- Select English, Chinese, French, Spanish, German, Japanese or Korean captions independently, or switch them off. In the webpage, captions sit below the picture to keep diagrams readable; fullscreen uses native video captions.
- Chapter buttons and transcript paragraphs seek to the selected narration’s corresponding explanation. Voice changes preserve the current semantic cue and its progress, rather than reusing elapsed seconds.
- **Take this scene into the lab** transfers the current positions, capacity and experiment mode. Video is paused while you explore.
- The sandbox uses capacity 2; the reference algorithm uses capacity 1. The selected-net experiment exposes each bounding box.
- Drag movable points, use arrow keys, or use the point selector and touch-friendly nudge buttons. A and D remain fixed.
- The companion reports real changes in wirelength and overflow. Suggestions are simulated before their predicted scores are displayed; they are possible experiments, not optimality guarantees.
- Reference mode steps through the actual 6 force updates, 3 averaging updates and 12 spread–reconnect pairs. Density weights can be compared from the same starting placement.
- Five concept checkpoints and a practical layout check provide feedback. The practical check accepts any arrangement satisfying the stated capacity condition; it does not require one exact coordinate answer.

## Narration and media

| Track | Voice | Measured programme length |
|---|---|---:|
| en_gb | en-GB-ThomasNeural | 6:38.196 |
| en_us | en-US-GuyNeural | 6:34.236 |
| en_in | en-IN-PrabhatNeural | 7:43.116 |
| zh | zh-CN-YunxiNeural | 6:55.476 |

Videos are H.264/AAC MP4, 1920 × 1080, 30 fps, with a low original music bed. Speech uses its natural rate and pitch. Programme durations differ because each voice is measured independently. English, Chinese and five translated caption sets are aligned within the same semantic cues; translated sentence timing is an approximation, not phoneme-level alignment. The five additional translations have not had independent native-speaker review.

## Editable source map

- `content/script.json`: the complete 39-cue English/Chinese narration and eight chapter definitions.
- `content/translations.json`, `caption-glossary.json`: French, Spanish, German, Japanese and Korean translations and shared terms.
- `scene.js`, `film-art.js`: the illustrated film and explanatory animations.
- `scientist-rig.js`, `scientist-art.js`: closed-mouth vector character, subtle moustache movement, coordinated hand-target gestures.
- `domain.js`, `board.js`: the shared point model, metrics, reference trace and diagram.
- `timeline.js`: normalized semantic cue states shared by video rendering and lab transfer.
- `lab.js`, `mentor.js`, `exercises.js`: experiments, local metric-based comments, questions and feedback.
- `player.js`, `app.js`, `index.html` and CSS: the learning website and media controls.
- `media/manifest.json`: four videos, 28 VTT caption files and the measured timing files.
- `CREDITS.md`, `assets/*provenance.json`, `content/voice-provenance.json`: source and adaptation records.

The scientist’s moustache is expressive animation, not an attempt at lip-reading or phoneme synchronisation. All interactive feedback runs on the device; the website makes no speech-service or language-model requests.

## Rebuild in the project workspace

The parent project retains production scripts under `scripts/` and raw speech clips, narration WAVs, music beds and picture masters under `production/`. These large editing intermediates are outside the portable website package.

```powershell
# From Placement_Lesson6, with the local server on port 8770:
python scripts/make_course_audio.py
python scripts/render_course.py --preview
python scripts/render_course.py --primary --fps 30
python scripts/render_course.py --assemble --fps 30
node scripts/check_course_domain.mjs
```

Other checks are `python scripts/check_course_audio.py`, `python scripts/check_course_film.py`, `python scripts/check_course_timeline.py`, `python scripts/check_course_lab.py`, and `python scripts/check_course_site.py`.

Rendering needs Python, the project Playwright package in `.pydeps`, local Chrome, FFmpeg and NumPy; speech generation also uses `edge_tts` and the authorised online service. Unchanged exact voice/text/rate clips are cached. Viewing the finished website does not need these production dependencies.

The primary HTML/SVG picture is rendered by Chromium. Each semantic picture clip is then matched to each narration’s measured cue window and assembled with that voice’s unmodified speech. This avoids reauthoring diagrams four times and retains equivalent cue progress in the interactive scene. Frame-boundary timing is accurate to within one 30 fps frame. No Pillow drawing is used.
