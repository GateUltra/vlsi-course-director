import {initialPositions, targetPositions, clone, clamp, smooth} from './domain.js';
// Deterministic random-access state: no wall clock, random numbers or mutable scene history.
export function stateAt(time, clock, script) {
  if (!Number.isFinite(time) || !clock.segments?.length) throw new TypeError('A finite time and cue clock are required.');
  const t = clamp(time, 0, clock.duration);
  const cue = clock.segments.find((s, i) => t < (s.sceneEnd ?? clock.segments[i + 1]?.start ?? clock.duration)) ?? clock.segments.at(-1);
  const progress = clamp((t - cue.start) / Math.max(.001, cue.sceneEnd - cue.start));
  const meta = script.cues.find(c => c.id === cue.id);
  if (!meta) throw new Error(`Missing script cue: ${cue.id}`);
  const positions = clone(initialPositions);
  if (cue.id === 'move') {
    const p = smooth(progress / .75);
    for (const axis of ['x', 'y']) positions.B[axis] += (targetPositions.B[axis] - positions.B[axis]) * p;
  }
  return {time: t, cueId: cue.id, progress, positions, title: meta.title, chapter: meta.chapter, text: meta.en, provisional: Boolean(clock.provisional)};
}
export function semanticPosition(time, clock) {
  const cue = clock.segments.find(s => time < s.sceneEnd) ?? clock.segments.at(-1);
  return {cueId: cue.id, progress: clamp((time - cue.start) / (cue.sceneEnd - cue.start))};
}
export function semanticTime(position, clock) {
  const cue = clock.segments.find(s => s.id === position.cueId);
  if (!cue) throw new Error(`Unknown cue: ${position.cueId}`);
  return cue.start + clamp(position.progress) * (cue.sceneEnd - cue.start);
}
