// This original two-pin example is a teaching proxy, not a placement solver.
export const initialPositions = {A: {x: 2, y: 2}, B: {x: 8, y: 7}};
export const targetPositions = {A: {x: 2, y: 2}, B: {x: 5, y: 4}};
// Numerical tolerance for repeated floating-point moves, not display rounding.
export const numericEpsilon = 1e-9;
export const clone = value => structuredClone(value);
export const clamp = (value, min = 0, max = 1) => Math.max(min, Math.min(max, value));
export const smooth = value => { const p = clamp(value); return p * p * (3 - 2 * p); };
export function metrics(positions) {
  const dx = Math.abs(positions.B.x - positions.A.x);
  const dy = Math.abs(positions.B.y - positions.A.y);
  return {dx, dy, wirelength: dx + dy};
}
export function moveB(positions, point) {
  if (![point.x, point.y].every(Number.isFinite)) throw new TypeError('Coordinates must be finite.');
  return {...clone(positions), B: {x: clamp(point.x, 0, 10), y: clamp(point.y, 0, 10)}};
}
export function grade(positions) {
  const length = metrics(positions).wirelength;
  const fixed = positions.A.x === 2 && positions.A.y === 2;
  const inside = Object.values(positions).every(p => [p.x, p.y].every(v => Number.isFinite(v) && v >= 0 && v <= 10));
  // Grade the actual state, never a display-rounded score. A reason lets the UI
  // distinguish values just outside a boundary even if both display as 3.0/6.0.
  const reason = !fixed ? 'fixed-pin' : !inside ? 'outside-board' : length < 3 - numericEpsilon ? 'below-minimum' : length > 6 + numericEpsilon ? 'above-maximum' : 'within-range';
  return {pass: reason === 'within-range', length, reason};
}
export function mentor(positions, previous = positions) {
  const current = metrics(positions).wirelength, before = metrics(previous).wirelength;
  const assessment = grade(positions);
  const delta = current - before;
  const change = Math.abs(delta) < .01 ? '' : `That move ${delta < 0 ? 'shortened' : 'lengthened'} the estimate by ${Math.abs(delta).toFixed(1)} units. `;
  if (assessment.reason === 'below-minimum') return change + 'Very short, but our exercise asks for 3–6 units. Move B a little farther from A.';
  if (assessment.pass) return change + 'This meets the exercise target. Can you find a different position with the same length?';
  if (assessment.reason !== 'above-maximum') return 'Reset the lab to restore fixed A and valid board coordinates.';
  // The suggested move is simulated with the same domain function as the lab.
  const candidate = moveB(positions, {x: positions.B.x + (2 - positions.B.x) * .35, y: positions.B.y + (2 - positions.B.y) * .35});
  return change + `Try moving B toward A. A 35% move in each direction would give ${metrics(candidate).wirelength.toFixed(1)} units.`;
}
