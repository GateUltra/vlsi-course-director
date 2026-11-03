# Video, voices, captions and music

## Timeline and rendering

Author stable IDs for scenes and short narration cues. Retain a canonical semantic script and the actual voice-specific clip files and boundary metadata. Synthesize or record each authorized voice, cache only exact text/voice/rate matches, measure the actual clip durations, and construct a separate cumulative clock for every voice. When content changes, invalidate affected cache and regenerate dependent timing, animation, captions and media; write manifest/timing files atomically to avoid partial reads.

Use voice-specific real boundaries to schedule important visual actions. A TTS service may report two spoken sentences as one boundary, or split the same meaning differently across languages. Match semantic groups against observed boundaries; when uncertain, hold a full cue or use a documented approximation rather than inventing word-level precision. Check the actual events against the spoken instruction, especially after edits.

Render native/editable diagrams as code or vector layers when they are useful for data-driven transformations. Choose rendering tools on actual availability and quality, not by mandate. Preserve a reproducible silent picture master, narration assets, assembly script and settings; verify the final audible export rather than treating the silent master as the final film.

## Voices and captions

Choose voices appropriate for the audience and requested language/accent, and prepare a small audition when the choice is uncertain. Names of public figures or broadcasters can describe a broad delivery style, but do not imply a real person's participation, approval or a voice clone. Respect the user's selection and any current requirements governing use of third-party voice services; never send protected material or bypass a declined action.

Keep narration choice independent from subtitle language. Translate by meaning and preserve a terminology glossary; align each target language to the actual clock of the selected voice. Make VTT for browsers and SRT where requested; support captions off. Verify monotonic start/end, non-overlap, video bounds, readable line length and common glyph rendering. Mechanical checks do not establish translation accuracy; seek human/native review where needed and label its absence.

## Music and mix

Find music with permission appropriate to the actual intended distribution, retain creator, exact track, source URL, license and a local license record; record edits and hashes. CC0 is useful when suitable but is not mandatory. Produce a low unobtrusive bed with fades and, when useful, speech-driven ducking; assess loudness and clipping and audition the result. Do not treat a single decibel value or an algorithmic loudness measurement as proof of intelligibility, loop quality or subjective approval.

## Quality checks

- Decode each final media file and confirm video, audible audio, expected length and seekability. Compare selected original clips against the exported soundtrack near expected starts, sampling beginning, middle, ending and changed cues; document thresholds and limitations.
- Compare representative frames to source diagrams and narration at actual timestamps, including transitions, geometry, labels and reading speed. Check long holds and confusing intermediate states.
- Check every requested audio/subtitle combination and timing, then perform real listening and playback when possible. If unavailable, distinguish technical verification from human audition rather than inventing an approval.
