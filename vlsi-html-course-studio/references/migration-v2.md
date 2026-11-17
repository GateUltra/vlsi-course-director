# Migration and controlled evolution

## One skill, one runtime, replaceable course packs

The engine supplies execution and checks. A pack supplies domain semantics, SVG diagrams, animation state, numeric/pointer actions, intent/narration/captions, exercises, assets and independent expected results. Code is a valid pack asset; moving formulas into JSON is not a portability requirement.

Within contract 1.0, new lessons change only their own pack. Record hashes of `assets/runtime/` and production scripts before and after migration. If a new interaction cannot be expressed through the contract, propose an engine candidate, test existing packs, update versions, then release. Do not fork a hidden engine per course.

The schema for shared intent remains stable. Each course has different intent data. Changing the domain model is expected; changing the shared player to understand that model indicates a boundary leak.

## Version and invalidation

- Engine release: production scripts and runtime (v2.0.0).
- Contract version: adapter/manifest interpretation (`1.0`). Unknown versions fail.
- Course version: authored lesson content, domain and tests; bump for released changes.
- Input identity: exact hashes detect edits even without a version bump.
- Build record: runtime, course and audio inputs, measured clocks, outputs and tool versions.

Narration/voice changes invalidate clip fingerprints, clocks, captions and pictures. Scene/model changes invalidate pictures and browser evidence, and require checking spoken numbers and exercises. Translation changes invalidate subtitles and their review. The v2 CLI rebuilds into a new output directory; correctness takes priority over a speculative incremental scheduler. Exact TTS caching still avoids unchanged synthesis.

`verify` checks recorded fingerprints and semantic cue coverage. This guards against accidental stale combinations; it is not a cryptographic publisher signature.

## Preserved baseline and original precision

The original v1 release is commit `dca1c25d2d8e6a944536274d05878904a2cc4d5f`, with a retained versioned download. `baseline-v1.json` records 123 original source/tool files. Old `vlsi-course-director/`, `assets/starter/`, `assets/placement-lesson06-source/` and the six legacy tools remain intact. The source snapshot is a worked precedent, not a silently converted v2 pack.

| Original precision | Where it belongs |
|---|---|
| Decimal-safe captions, independent voice clocks, caption off/fullscreen | Common audio/runtime checks |
| Exact frame transfer, request-token voice switching, multiple answers | Runtime contract and browser regressions |
| Placement fixed points, bin boundaries, capacities, reference update order | Preserved domain and course-specific tests |
| 0.8-second intro/tail and thought pauses | Course timing and hold settings |
| Voice IDs, speed/pitch, optional background music | Course audio configuration and measured evidence |
| Two-bone IK, closed mouth, tiny moustache, text safe areas | Course visual implementation; original code/rationale retained |
| 39-cue production vs 3-cue benchmark | Different deliverables; benchmark success does not re-certify the full film |

The v2 samples use a shared presentation shell. They do not claim pixel equivalence with the original 39-scene Placement film. Maintaining that film can continue through its preserved source. A full conversion would need visual and numerical regression against the original; do not overwrite it to make an abstraction appear complete.

## Acceptance before release

1. Check positive and negative contracts: added cue with stale audio/clock, unknown scene, edited source, damaged clip and altered output.
2. Build real narration from checked-in audio in an isolated dependency environment; inspect video and browser behavior.
3. Independently author a different knowledge structure against the contract, using unchanged engine hashes.
4. Record supported tool/OS versions, executed checks, review limits and manual interventions. An isolated Windows venv is not another operating system.
5. Release after evidence passes; preserve the old release and baseline for rollback.
