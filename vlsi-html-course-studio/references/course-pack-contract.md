# Course pack contract 1.0 — engine 2.0.0

This is the executable boundary for new HTML/SVG courses. Existing Placement source remains an immutable reference. Course-specific code, diagrams, text, art, exercises and tests belong in a course pack; the runtime and production scripts do not import a particular lesson.

## Files and manifest

The pack root contains `lesson.json`, the JS ES module named by `adapter` (normally `adapter.mjs`), `check.mjs` containing independent domain expectations, and optional assets and `audio/fixtures.json`. Relative paths must resolve inside the pack. No browser code may require private paths, remote libraries or unrecorded source assets.

`lesson.json` fields:

```json
{
  "contractVersion": "1.0", "id": "course-id", "version": "1.0.0",
  "title": "Lesson title", "description": "Scope and simplifications",
  "adapter": "adapter.mjs", "defaultVoice": "en_gb",
  "voices": [
    {"id":"en_gb","language":"en","label":"British English","provider":"edge_tts","voice":"en-GB-ThomasNeural","rate":"+0%","pitch":"+0Hz"},
    {"id":"zh","language":"zh","label":"普通话","provider":"edge_tts","voice":"zh-CN-YunxiNeural","rate":"+0%","pitch":"+0Hz"}
  ],
  "captionLanguages": ["en", "zh"], "timing":{"intro":0.3,"tail":0.3},
  "cues": [{
    "id":"unique-cue","chapter":"01","title":"A meaningful action",
    "intent":"What this cue makes observable", "sceneId":"implemented-scene",
    "narration":{"en":"Actual spoken words.","zh":"实际旁白。"},
    "captions":{"en":"Actual spoken words.","zh":"实际旁白。"},
    "holdAfter":0.4
  }],
  "exercises":[{"id":"exercise-id","cueId":"unique-cue","prompt":"An observable target","config":{}}],
  "audioFixtures":"audio/fixtures.json"
}
```

All IDs are unique nonempty ASCII identifiers `[a-zA-Z0-9_-]+`. Cues, voices, captions and exercises are nonempty. Voice language text and every declared subtitle language must exist for every cue. Numbers must be finite. Chapters are derived from cues in first-occurrence order. `sceneId` must be declared by the adapter; an unknown scene is an error, not a blank or generic scene. A pack may add domain data under extra fields or in local module assets. Manifest version and adapter API versions are independent of engine release versions.

## Adapter API (ES module, browser and Node compatible)

Required exports:

```js
export const apiVersion = '1.0';
export const sceneIds = ['implemented-scene'];
export function initialState(course) { /* JSON-serializable state */ }
export function validateState(state) { /* throw on invalid state */ }
export function stateAt(cue, progress, course) { /* deterministic, progress in [0,1] */ }
export function render(state, {mode, cue, progress}) { /* complete SVG string, viewBox="0 0 1000 560" */ }
export function controls(state) { /* [{id,label,value,min,max,step}] numeric controls */ }
export function reduce(state, action) { /* action={type:'set',id,value}; new state, no mutation */ }
export function metrics(state) { /* [{id,label,value,unit?}], finite numeric values */ }
export function feedback(state, previousState) { /* {text,tone:'neutral'|'good'|'warn'} */ }
export function grade(state, exercise) { /* {pass:boolean,feedback:string} */ }
```

Optional `pointerAction(state, {x,y})` receives normalized coordinates in the SVG rectangle `[0,1]²`, and returns an action for `reduce` or null. The runtime handles pointer capture, keyboard-accessible controls, reset, and transfer; it does not know what a pin, gate or path is. Adapter render functions should escape any dynamic text. The pack is trusted executable code, not an untrusted upload sandbox.

`stateAt` and `render` must support random access without prior frames, system time or unseeded randomness. Model functions must not mutate inputs. Control IDs must remain stable during interaction; values and limits may change. `validateState` returns normally for valid input and throws for invalid input. Domain boundary rules, tolerances, expected examples and alternative correct exercise answers belong in pack `check.mjs`; common contract tests are additional checks, not an independent scientific oracle.

## Shared snapshots and timing

The engine creates `{contractVersion:'1.0',courseId,courseVersion,cueId,progress,state}`. Transfer pauses the movie, uses its selected voice clock, takes a deep copy of exact `stateAt`, validates it, and rejects a different pack/version. `state` is opaque to the runtime. Every transfer-supported scene must describe a valid interactive state, including intermediate frames. Reset returns the imported snapshot.

Each voice gets a measured clock with `id`, `duration`, `segments:[{id,start,end,sceneEnd}]`, exact cue order, text hashes and build identity. `start..end` is speech; `end..sceneEnd` is its explicit hold. Intro/tail are explicit (default 0.3 seconds each). Never reuse an old clock after changing any narration. Version records bind course content, adapter/runtime code, audio bytes, captions and media to one build. The renderer must expose and validate `window.clock` and `window.buildIdentity`; missing identity fails the v2 build even though the legacy standalone renderer permits optional clocks.

## Offline audio and online synthesis

`audio/fixtures.json` has `schemaVersion:'1.0'` and a `clips` list. Each clip records `voiceId`, `cueId`, `path` (relative to pack), `sha256` of exact bytes, `textSha256` of UTF-8 narration, `voice`, `rate`, `pitch`, and `provenance` with provider/source. Every selected voice/cue pair must occur exactly once; missing, duplicate, extra or stale clips fail. Fixture audio is immutable input, not a promise of bit-identical future online synthesis.

Production CLI modes: `fixture` requires verified local clips; `tts` explicitly uses online edge-tts with bounded retries and exact text/voice/settings cache keys. Contract 1.0's voice configuration currently uses the `edge_tts` provider identity in both modes; other speech/recording providers require an explicit adapter extension. No silent fallback between modes or voices. Generic build CLI measures audio, creates clocks/captions, renders each requested voice from the same runtime, muxes, validates and publishes to a new output directory only after success. Builds are offline in fixture mode. Optional licensed background music can be a pack-relative `bgm` path with `bgmGain` in [0,0.3]; keep clean narration masters separately.

Each media track retains `video` for the H.264/AAC MP4 and lists ordered `sources:[{src,type}]` for MP4 and VP8/Opus WebM. The player selects a format supported by `canPlayType`; both carry the same voice and semantic clock. This is a codec choice, not a voice/content fallback. Both files must be present, hashed and fully decoded during verification. Open-source Chromium builds can lack H.264/AAC even when rendering works; the WebM alternative is part of the offline reproduction path.

## Acceptance and change scope

Before expensive generation: validate pack, dependencies, adapter scene coverage, domain tests and fixture completeness (fixture mode). Before declaring a build usable: check every track, exact cue/caption coverage, audio/video stream duration and decode, source fingerprints, browser controls and exact snapshot transfer. Subjective clarity, speech and translation review remain separately reported.

Supported migration target: deterministic 2D SVG diagrams with JSON state, numeric lab controls and/or normalized pointer actions. A new course within this scope modifies only its pack. A new interaction paradigm requires an explicit engine candidate, compatibility tests and a versioned release, not hidden patches to the installed shared runtime.
