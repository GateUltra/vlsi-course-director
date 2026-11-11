import {Board, escapeText} from './board.js';
import {metrics} from './domain.js';
// The original vector companion has a fixed closed smile; no mouth animation.
export function Scientist() {
  return `<svg viewBox="0 0 180 190" xmlns="http://www.w3.org/2000/svg" aria-label="Cartoon science companion"><path d="M31 188Q25 122 90 122Q155 122 149 188" fill="#fffdf7" stroke="#397f75" stroke-width="4"/><path d="M61 141L90 173L119 141" fill="#b8d4cd"/><path d="M49 43Q15 49 34 75Q12 91 47 102M132 44Q163 52 147 74Q171 93 135 104" fill="#fffdf7" stroke="#809c8c" stroke-width="3"/><ellipse cx="90" cy="78" rx="48" ry="57" fill="#efcfae"/><path d="M48 46Q50 8 86 27Q127 4 135 46" fill="#fffdf7" stroke="#809c8c" stroke-width="3"/><g fill="none" stroke="#355f55" stroke-width="4"><circle cx="70" cy="74" r="15"/><circle cx="111" cy="74" r="15"/><path d="M85 74H96"/></g><g fill="#355f55"><circle cx="71" cy="74" r="3"/><circle cx="110" cy="74" r="3"/></g><path d="M82 94Q90 98 98 94" fill="none" stroke="#9c6c52" stroke-width="3"/><path d="M66 109Q90 116 114 109" fill="none" stroke="#9c6c52" stroke-width="3"/><path d="M65 105Q74 94 90 103Q108 93 117 105Q104 116 90 108Q77 115 65 105" fill="#fffdf7"/></svg>`;
}
export function Scene(state) {
  const m = metrics(state.positions);
  return `<section class="scene" aria-label="${escapeText(state.title)}"><div class="scene-copy"><span class="eyebrow">${escapeText(state.chapter)} / WIRELENGTH STUDIO</span><h2>${escapeText(state.title)}</h2><p>${escapeText(state.text)}</p><div class="formula">${m.dx.toFixed(1)} + ${m.dy.toFixed(1)} <strong>≈ ${m.wirelength.toFixed(1)}</strong><small>Manhattan distance · units · values rounded</small></div><div class="scene-guide">${Scientist()}<span>A useful estimate.<br>Not a routed wire.</span></div></div><div class="scene-board">${Board(state, {id: 'film-board'})}</div></section>`;
}
