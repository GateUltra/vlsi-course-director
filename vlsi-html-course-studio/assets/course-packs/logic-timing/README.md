# Logic timing — independent course-pack migration

This pack was authored from `references/course-pack-contract.md` without reading the generic runtime or the wirelength pack. Its production boundary is the contract, not implementation details. All code, model data, SVG artwork, narration, subtitles and independent domain assertions are inside this directory. Audio fixtures are generated separately from the frozen narration and recorded with hashes.

The initial example has upper/lower/final delays of 2/5/1 ns. Output arrival is 6 ns; raising the upper delay to 7 ns changes the critical branch and gives 8 ns. The exercise accepts many combinations with a uniquely critical upper branch and arrival no greater than 6 ns. At equality both branches are critical. A numerical tolerance of `1e-9` handles arithmetic noise; displayed rounding is never the grading rule.

This is an original educational max-plus model. Input arrival is zero and all delays are constant positive numbers. Reconvergent logic sensitization, routing, load, transition slew, variation, clock domains and setup/hold checks are deliberately excluded. Neither the output value nor the exercise is a full STA/signoff result.

Run `node check.mjs` here for independent domain tests. To build, use the common skill CLI and this directory as `--course`; no engine edits are part of this pack. The three scenes deliberately expose the same JSON state and numeric controls to video and lab. The runtime decides when to call them; it need not understand gates or paths.

Original text/code/art are under the repository MIT license. Synthetic audio provenance and distribution information are recorded in `audio/fixtures.json` when the fixtures are prepared. No third-party artwork or imported course code is used.
