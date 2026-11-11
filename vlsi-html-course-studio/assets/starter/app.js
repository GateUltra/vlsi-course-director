import {clone, initialPositions, metrics, moveB, grade, mentor} from './domain.js';
import {Board, boardToWorld} from './board.js';
import {Scene, Scientist} from './scene.js';
import {stateAt} from './timeline.js';
const $ = selector => document.querySelector(selector);
async function data(path) { const response = await fetch(path); if (!response.ok) throw new Error(`Missing ${path}`); return response.json(); }
const [script, clock] = await Promise.all([data('content/script.json'), data('content/demo-clock.json')]);
document.title = `${script.title} · silent storyboard`; $('#course-title').textContent = script.title;
let time = 0, playing = false, previousFrame = null, filmState, labState = {positions: clone(initialPositions), source: 'Initial example'};
$('#seek').max = clock.duration;
for (const cue of script.cues) {
  const button = document.createElement('button'); button.textContent = `${cue.chapter} / ${cue.title}`; button.dataset.cue = cue.id;
  button.onclick = () => { playing = false; drawFilm(clock.segments.find(s => s.id === cue.id).start); };
  $('#chapters').append(button);
}
function drawReadout(selector, state) {
  const {A, B} = state.positions, m = metrics(state.positions);
  // Ordinary HTML remains readable when the SVG is scaled down on a phone.
  $(selector).innerHTML = `<dl><div><dt>Pin A · fixed</dt><dd>(${A.x.toFixed(2)}, ${A.y.toFixed(2)})</dd></div><div><dt>Pin B · movable</dt><dd>(${B.x.toFixed(2)}, ${B.y.toFixed(2)})</dd></div><div><dt>Box width / height</dt><dd>${m.dx.toFixed(2)} / ${m.dy.toFixed(2)} units</dd></div><div><dt>Width + height</dt><dd>≈ ${m.wirelength.toFixed(2)} units</dd></div></dl>`;
}
function drawFilm(value) {
  time = Math.max(0, Math.min(clock.duration, value)); filmState = stateAt(time, clock, script);
  $('#film-frame').innerHTML = Scene(filmState); $('#seek').value = time; $('#time').textContent = `${time.toFixed(1)} s`;
  $('#play').textContent = playing ? 'Pause storyboard' : 'Play storyboard';
  $('#spoken-text').textContent = `Current cue: ${filmState.title} Draft narration: ${filmState.text}`;
  drawReadout('#film-readout', filmState);
  document.querySelectorAll('#chapters button').forEach(button => {if(button.dataset.cue === filmState.cueId) button.setAttribute('aria-current', 'step'); else button.removeAttribute('aria-current');});
}
function drawLab(previous = labState.positions, {comment = true, restoreFocus = false} = {}) {
  $('#lab-board').innerHTML = Board(labState, {interactive: true, id: 'interactive-board'});
  $('#score').textContent = `Estimated length (rounded): ${metrics(labState.positions).wirelength.toFixed(1)} units`;
  drawReadout('#lab-readout', labState);
  if (comment) $('#mentor').textContent = mentor(labState.positions, previous);
  if (restoreFocus) $('#lab-board [data-pin="B"]').focus({preventScroll: true});
}
function apply(point, options = {}) {
  const previous = clone(labState.positions); labState.positions = moveB(labState.positions, point); drawLab(previous, options); $('#feedback').textContent = '';
}
$('#companion').innerHTML = Scientist();
$('#play').onclick = () => {if(time >= clock.duration) time = 0; playing = !playing; drawFilm(time);};
$('#seek').oninput = event => { playing = false; drawFilm(Number(event.target.value)); };
$('#transfer').onclick = () => {
  playing = false; drawFilm(time); labState = {...clone(filmState), source: `Storyboard ${filmState.cueId} at ${time.toFixed(2)} seconds`};
  $('#transfer-status').textContent = `Transferred the exact paused state: ${labState.source}. A stays fixed; move B to investigate.`;
  drawLab(); $('#feedback').textContent = ''; $('#lab').scrollIntoView({behavior: matchMedia('(prefers-reduced-motion: reduce)').matches ? 'instant' : 'smooth'});
};
$('#reset').onclick = () => { labState = {positions: clone(initialPositions), source: 'Initial example'}; $('#transfer-status').textContent = 'Reset to the initial example. A stays fixed at (2, 2).'; drawLab(); $('#feedback').textContent = ''; };
document.querySelectorAll('[data-dx]').forEach(button => button.onclick = () => apply({x: labState.positions.B.x + Number(button.dataset.dx), y: labState.positions.B.y + Number(button.dataset.dy)}));
$('#lab-board').addEventListener('keydown', event => {
  if (!event.target.closest('[data-pin="B"]')) return;
  const step = event.shiftKey ? .1 : .5, delta = {ArrowLeft: [-step, 0], ArrowRight: [step, 0], ArrowUp: [0, step], ArrowDown: [0, -step]}[event.key];
  if (!delta) return; event.preventDefault(); apply({x: labState.positions.B.x + delta[0], y: labState.positions.B.y + delta[1]}, {restoreFocus: true});
});
let drag = null;
function pointFromEvent(event) {
  const svg = $('#interactive-board'), point = new DOMPoint(event.clientX, event.clientY).matrixTransform(svg.getScreenCTM().inverse());
  return boardToWorld(point);
}
$('#lab-board').addEventListener('pointerdown', event => {
  if (!event.target.closest('[data-pin="B"]')) return;
  event.preventDefault(); drag = {id: event.pointerId, before: clone(labState.positions)};
  $('#lab-board').setPointerCapture(event.pointerId); apply(pointFromEvent(event), {comment: false});
});
$('#lab-board').addEventListener('pointermove', event => {if(drag?.id === event.pointerId) apply(pointFromEvent(event), {comment: false});});
function endDrag(event) {if(drag?.id !== event.pointerId) return; $('#mentor').textContent = mentor(labState.positions, drag.before); drag = null;}
$('#lab-board').addEventListener('pointerup', endDrag); $('#lab-board').addEventListener('pointercancel', endDrag);
$('#check').onclick = () => {
  const result = grade(labState.positions);
  const messages = {
    'within-range': 'Yes — the unrounded estimate is within 3–6 units, including the endpoints. Many positions work. Try a different one with the same total.',
    'below-minimum': 'Not yet — the unrounded estimate is below the 3-unit minimum. The displayed score is rounded; move B a little farther from A.',
    'above-maximum': 'Not yet — the unrounded estimate is above the 6-unit maximum. The displayed score is rounded; move B a little closer to A.',
    'fixed-pin': 'A must stay fixed at (2, 2). Reset the lab and move only B.',
    'outside-board': 'Both pins must have finite coordinates inside the board. Reset the lab and try again.'
  };
  $('#feedback').textContent = messages[result.reason];
};
drawFilm(0); drawLab();
function tick(now) {if(previousFrame !== null && playing) { const next = time + Math.min(.1, (now - previousFrame) / 1000); if(next >= clock.duration) playing = false; drawFilm(next); } previousFrame = now; requestAnimationFrame(tick);}
requestAnimationFrame(tick);
window.starter = {getFilmState: () => clone(filmState), getLabState: () => clone(labState), seek: value => {playing = false; drawFilm(value);}, setB: point => apply(point)};
window.ready = true;
