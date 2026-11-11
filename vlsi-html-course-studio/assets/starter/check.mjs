import assert from 'node:assert/strict';
import {readFile} from 'node:fs/promises';
import {initialPositions, metrics, moveB, grade, mentor} from './domain.js';
import {stateAt, semanticPosition, semanticTime} from './timeline.js';
import {Board, worldToBoard, boardToWorld} from './board.js';
const script = JSON.parse(await readFile(new URL('./content/script.json', import.meta.url)));
const clock = JSON.parse(await readFile(new URL('./content/demo-clock.json', import.meta.url)));
assert.equal(metrics(initialPositions).wirelength, 11);
const altered = moveB(initialPositions, {x: 5, y: 4});
assert.equal(metrics(altered).wirelength, 5);
assert.equal(initialPositions.B.x, 8, 'A move must not mutate the source snapshot.');
assert.deepEqual(altered.A, initialPositions.A);
assert.equal(grade(altered).pass, true);
assert.equal(grade(moveB(initialPositions, {x: 2, y: 7})).pass, true, 'Different valid coordinates must pass.');
assert.equal(grade(initialPositions).pass, false);
assert.equal(grade(moveB(initialPositions, {x: 2, y: 2})).pass, false);
assert.equal(grade({...altered, A: {x: 3, y: 2}}).pass, false);
// Dragging and film transfer can create sub-tenth coordinates. Display rounding
// must not change the inclusive 3–6 range or obscure which boundary was crossed.
const justAbove = grade(moveB(initialPositions, {x: 5.03, y: 5}));
assert.equal(justAbove.length.toFixed(1), '6.0');
assert.equal(justAbove.pass, false);
assert.equal(justAbove.reason, 'above-maximum');
const justBelow = grade(moveB(initialPositions, {x: 4.99, y: 2}));
assert.equal(justBelow.length.toFixed(1), '3.0');
assert.equal(justBelow.pass, false);
assert.equal(justBelow.reason, 'below-minimum');
for (const x of [5, 5.01, 7.99, 8]) {
  const boundaryOrInside = grade(moveB(initialPositions, {x, y: 2}));
  assert.equal(boundaryOrInside.pass, true);
  assert.equal(boundaryOrInside.reason, 'within-range');
}
let keyboardPositions = structuredClone(initialPositions);
for (let i = 0; i < 50; i++) keyboardPositions = moveB(keyboardPositions, {x: keyboardPositions.B.x, y: keyboardPositions.B.y - .1});
assert.ok(Math.abs(keyboardPositions.B.y - 2) < 1e-12);
assert.equal(grade(keyboardPositions).pass, true, 'Floating-point accumulation must not reject a mathematically exact endpoint.');
assert.match(mentor(keyboardPositions), /meets the exercise target/);
assert.equal(grade(moveB(initialPositions, {x: 8.000001, y: 2})).pass, false, 'Numeric tolerance must not become display-rounding tolerance.');
assert.throws(() => moveB(initialPositions, {x: NaN, y: 1}));
assert.deepEqual(moveB(initialPositions, {x: 20, y: -1}).B, {x: 10, y: 0});
assert.match(mentor(altered, initialPositions), /shortened.*6\.0/);
assert.match(mentor(initialPositions), /7\.2/);
for (const time of [0, 7.99, 8, 15, 20, 23.7, 31.9, 32]) {
  const first = stateAt(time, clock, script); stateAt(10, clock, script);
  assert.deepEqual(stateAt(time, clock, script), first, 'Random-access rendering must be deterministic.');
  assert.ok(Math.abs(semanticTime(semanticPosition(time, clock), clock) - time) < 1e-10);
  const clone = structuredClone(first); clone.positions.B.x = 100;
  assert.notEqual(stateAt(time, clock, script).positions.B.x, 100);
  assert.match(Board(first), /<svg/);
}
assert.equal(stateAt(8, clock, script).cueId, 'measure');
assert.equal(stateAt(32, clock, script).positions.B.x, 5);
const p = {x: 2.3, y: 7.1}, roundtrip = boardToWorld(worldToBoard(p));
assert.ok(Math.abs(p.x - roundtrip.x) < 1e-10 && Math.abs(p.y - roundtrip.y) < 1e-10);
console.log(JSON.stringify({ok: true, checks: 'metrics, alternate exercise solutions, fixed pin, clamping, metric comments, semantic mapping, deterministic random access, shared board'}, null, 2));
