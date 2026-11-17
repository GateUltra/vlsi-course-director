# Reproduce a complete small course

## What this proves

The bundled packs have real fixed narration and translations. Fixture mode reconstructs a complete video, independent captions, a player, an exact scene transfer and a working exercise without calling TTS. `wirelength` and `logic-timing` use different domain states and the same runtime. These are short engineering benchmarks, not complete replacements for a full lesson's research, direction or human review.

The required external tools are Python 3.10+, Node 18+, FFmpeg/ffprobe with libx264/AAC and libvpx/libopus encoders, and Playwright Chromium. Tested versions and actual platform are recorded in the release evidence. The Python entry dependencies are pinned in `requirements.txt`; `requirements-lock-windows-py311.txt` also records the full tested Python dependency set. Existing system tools are discovered and checked; they are not bundled.

## Isolated setup (PowerShell)

Run from the `vlsi-html-course-studio` folder. Use a fresh environment, not an earlier course's `.pydeps`.

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-lock-windows-py311.txt
.\.venv\Scripts\python.exe -m playwright install chromium
.\.venv\Scripts\python.exe scripts/studio.py doctor
```

Node and FFmpeg/ffprobe must be on PATH, or use the CLI's explicit executable parameters. If Chromium is already installed, use `--browser` with its executable. A clean Ubuntu 24.04 hosted runner has also passed both full builds and browser checks; use `.venv/bin/python` on that OS. The exact setup/build commands and tested platform are in the [public CI workflow](https://github.com/GateUltra/vlsi-course-director/blob/main/.github/workflows/studio-v2.yml). Do not substitute an untested `ubuntu-latest` when the pinned browser version has a narrower support matrix. [Playwright installation](https://playwright.dev/python/docs/library) distinguishes its Python package from its browser download.

## Offline full build

```powershell
.\.venv\Scripts\python.exe scripts/studio.py check --course assets/course-packs/wirelength --audio-mode fixture
.\.venv\Scripts\python.exe scripts/studio.py build --course assets/course-packs/wirelength --out ./build-wirelength --audio-mode fixture --width 1280 --height 720 --fps 30
.\.venv\Scripts\python.exe scripts/studio.py verify --site ./build-wirelength
.\.venv\Scripts\python.exe scripts/check_studio_browser.py --site ./build-wirelength --report ./wirelength-browser.json
.\.venv\Scripts\python.exe scripts/serve_studio.py --directory ./build-wirelength --port 8780
```

Open `http://127.0.0.1:8780/`. The build directory must not already exist; choose a new name for another run. It is a portable static site with real MP4/VTT assets, not a reference to the author's computer. Do not open `index.html` with `file://`: browser modules, fetch and subtitles need HTTP. Static hosts can serve the output without Python/TTS at viewing time.

Build the other pack by changing only `--course assets/course-packs/logic-timing` and output paths. No renderer, player, timing code or audio code changes are needed.

## Author a new course

1. Copy one pack into your own project. Change its identity/version and implement the model and tests from actual sources; do not edit installed runtime files.
2. Follow [contract 1.0](course-pack-contract.md). Keep cue intent, scene reference, narration, captions and exercise linkage in `lesson.json`. Implement all declared scenes and independent expected values in `check.mjs`.
3. Run `studio.py check --course YOUR_PACK` before creating audio. Optional `--audio-mode fixture` also checks the complete fixed audio set.
4. Use the explicit online synthesis command below after the current task authorizes transmission, then freeze the generated inputs. Other recording providers need an explicit adapter extension; v1.0 voice configuration uses edge_tts identities.
5. Build, verify, inspect representative full-size frames, listen, and test the actual interaction. A passing codec/hash report does not certify explanation or translation quality.

## Online speech is a separate operation

The production adapter uses [edge-tts](https://github.com/rany2/edge-tts). It requires a reachable service and available voice IDs. Voice settings live in the pack, not the engine. Do not promise perpetual free access or identical future waveforms.

To create a portable fixed input set for a new course whose `audio/` directory does not exist:

```powershell
.\.venv\Scripts\python.exe scripts/studio.py freeze-audio --course YOUR_PACK --out YOUR_PACK/audio
```

It writes audio bytes and `fixtures.json` with voice/settings, exact text hashes, file hashes and provenance. A changed narration must not use old fixtures. Keep the prior pack version and create a new version with a fresh audio destination; update `audioFixtures` accordingly. Fixture creation refuses an existing destination. Do not delete old approved audio merely to bypass that protection.

For a direct online course build use `build --audio-mode tts`; consult `--help` for cache configuration. It explicitly calls the service, uses bounded retries and fails when the requested voice/audio cannot be produced. There is no automatic substitute voice or silent movie fallback. Fixed cached inputs test the engineering chain; online synthesis tests the external adapter.

## Understanding evidence

- Domain tests check expected mathematics independently of the common engine.
- Adapter checks validate scene coverage, serializable states, purity, random access and control/metric/feedback interfaces.
- Build verification checks source identity, current cue sequence, complete captions, audio/video streams and output hashes.
- Real browser checks cover playback, voice/caption/speed changes, chapter navigation, exact snapshot import, controls, feedback, grading and mobile layout.
- Subjective review records clarity, voice, pacing and translations separately.

Failures should name the missing or stale input. Do not fix a failed check by removing metadata, relabelling a provisional clock or accepting a different voice. If the desired capability exceeds contract 1.0, follow [controlled evolution](migration-v2.md).

On a managed desktop sandbox, launching the local browser/server may require the normal execution permission escalation. This is distinct from a missing package; use the environment's approval mechanism rather than disabling sandbox protections. Normal local terminals use the same documented commands.

The generated site includes both MP4 (H.264/AAC) and WebM (VP8/Opus). The player chooses a supported format because some open-source Chromium builds cannot decode proprietary codecs. Both variants are verified; a successful frame renderer alone is not evidence of video playback.
