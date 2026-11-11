import {metrics} from './domain.js';
export const escapeText = value => String(value).replace(/[&<>"']/g, c => ({'&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'}[c]));
export const worldToBoard = p => ({x: 52 + 45 * p.x, y: 498 - 45 * p.y});
export const boardToWorld = p => ({x: (p.x - 52) / 45, y: (498 - p.y) / 45});
export function Board(state, {interactive = false, id = 'board'} = {}) {
  const {positions} = state, a = worldToBoard(positions.A), b = worldToBoard(positions.B), m = metrics(positions);
  const grid = Array.from({length: 11}, (_, i) => `<path d="M${52 + i * 45} 48V498 M52 ${498 - i * 45}H502"/>`).join('');
  const pins = Object.entries(positions).map(([name, position]) => {
    const p = worldToBoard(position), active = interactive && name === 'B';
    return `<g class="pin${active ? ' movable' : ''}" data-pin="${name}" ${active ? 'tabindex="0" role="button" aria-label="Pin B, use arrow keys to move"' : ''} transform="translate(${p.x} ${p.y})"><circle r="19" fill="${name === 'A' ? '#397f75' : '#c56870'}"/><text y="6" text-anchor="middle" fill="white" font-size="18" font-weight="700">${name}</text></g>`;
  }).join('');
  return `<svg id="${escapeText(id)}" class="shared-board" viewBox="0 0 554 554" xmlns="http://www.w3.org/2000/svg" aria-label="Two-pin wirelength diagram"><rect width="554" height="554" rx="22" fill="#fffdf7"/><g stroke="#dde4d8" stroke-width="1">${grid}</g><rect x="52" y="48" width="450" height="450" fill="none" stroke="#809c8c" stroke-width="2"/><path d="M${a.x} ${a.y}H${b.x}V${b.y}" fill="none" stroke="#ba8536" stroke-width="7" stroke-linecap="round" stroke-dasharray="10 7"/><rect x="${Math.min(a.x, b.x)}" y="${Math.min(a.y, b.y)}" width="${Math.abs(a.x - b.x)}" height="${Math.abs(a.y - b.y)}" fill="#f0c86c" fill-opacity=".12" stroke="#ba8536" stroke-width="2"/><text x="277" y="27" text-anchor="middle" font-size="15" fill="#456559">Bounding box: ${m.dx.toFixed(1)} wide × ${m.dy.toFixed(1)} high</text><text x="277" y="535" text-anchor="middle" font-size="17" fill="#456559">Width + height = ${m.wirelength.toFixed(1)} units</text>${pins}</svg>`;
}
