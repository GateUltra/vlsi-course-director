import {escapeText as esc, snapshotAt} from './core.mjs';
function lines(text, max = 54) {
  const result = []; let current = '';
  for (const word of String(text).split(/\s+/)) {
    if (current && current.length + word.length > max) { result.push(current); current = word; }
    else current += `${current ? ' ' : ''}${word}`;
  }
  if (current) result.push(current);
  return result;
}
export function scientist(progress = 0, small = false) {
  const bob = Math.sin(progress * Math.PI * 2) * .35;
  return `<g aria-label="A thoughtful science companion" transform="translate(0 ${bob})">
    ${small ? '' : '<path d="M-72 120 Q-98 190 -85 274 L88 274 Q100 190 72 120Z" fill="#f8faf7" stroke="#254e52" stroke-width="5"/><path d="M-12 141 L0 188 13 141" fill="#de8a66"/><path d="M-65 155 Q-107 159 -115 113 M65 155 Q102 165 112 201" fill="none" stroke="#254e52" stroke-width="28" stroke-linecap="round"/><path d="M-65 155 Q-107 159 -115 113 M65 155 Q102 165 112 201" fill="none" stroke="#f8faf7" stroke-width="20" stroke-linecap="round"/><circle cx="-115" cy="108" r="15" fill="#e9b88e"/><circle cx="114" cy="205" r="15" fill="#e9b88e"/>'}
    <path d="M-63 23 L-90 2 -73-5 -95-21 -65-25 -78-45 -42-47 -30-66 0-57 28-67 45-48 79-43 68-25 96-16 76 0 91 16 63 30Z" fill="#f8faf7" stroke="#254e52" stroke-width="4"/>
    <ellipse cx="0" cy="42" rx="64" ry="76" fill="#e9b88e" stroke="#254e52" stroke-width="4"/>
    <path d="M-56-8 Q-43-47-7-33 Q5-45 36-31 Q57-22 57 0 Q18-20-5-9 Q-29-20-56-8" fill="#fffdf6"/>
    <path d="M-44 22 Q-28 13-14 21 M15 21 Q31 13 45 22" fill="none" stroke="#fffdf6" stroke-width="11" stroke-linecap="round"/>
    <circle cx="-28" cy="34" r="5" fill="#254e52"/><circle cx="28" cy="34" r="5" fill="#254e52"/>
    <path d="M-4 35 L-10 58 Q0 63 10 56" fill="none" stroke="#bd8264" stroke-width="4" stroke-linecap="round"/>
    <path d="M0 66 Q-23 50-44 75 Q-20 88 0 75 Q20 88 44 75 Q23 50 0 66Z" fill="#fffdf6" transform="translate(0 ${bob*.4})"/>
    <path d="M-14 88 Q0 94 14 88" fill="none" stroke="#754e40" stroke-width="3" stroke-linecap="round"/>
  </g>`;
}
export function sceneAt(time, clock, course, adapter) {
  const snapshot = snapshotAt(time, clock, course, adapter);
  const cue = course.cues.find(item => item.id === snapshot.cueId);
  const metrics = adapter.metrics(snapshot.state);
  const diagram = adapter.render(snapshot.state,{mode:'film',cue,progress:snapshot.progress});
  if (typeof diagram !== 'string' || !/<svg\b/.test(diagram)) throw new Error('Adapter render must return SVG');
  // Preserve adapter typography/accessibility; only the enclosing viewport belongs
  // to the film shell. Keep scientific content above native fullscreen captions.
  const nested = diagram.replace(/<svg\b([^>]*)>/, (_, attributes) => {
    const preserved = attributes.replace(/\s(?:x|y|width|height)\s*=\s*(?:"[^"]*"|'[^']*')/g, '');
    return `<svg${preserved} x="62" y="225" width="1375" height="640">`;
  });
  const titleLines = lines(cue.title,40);
  const intentLines = lines(cue.intent,90);
  return {snapshot,svg:`<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1920 1080" width="1920" height="1080" font-family="Arial,Helvetica,sans-serif" role="img" aria-label="${esc(cue.title)}">
    <defs><pattern id="paper-grid" width="36" height="36" patternUnits="userSpaceOnUse"><circle cx="2" cy="2" r="1.3" fill="#d8dfd2"/></pattern><linearGradient id="panel-fill"><stop stop-color="#fffdf8"/><stop offset="1" stop-color="#f1f5ec"/></linearGradient></defs>
    <rect width="1920" height="1080" fill="#f8f3e6"/><rect width="1920" height="1080" fill="url(#paper-grid)" opacity=".6"/>
    <rect x="60" y="48" width="330" height="44" rx="22" fill="#dcebe0"/><text x="84" y="78" font-family="Arial,sans-serif" font-size="22" font-weight="700" letter-spacing="3" fill="#28645f">${esc(cue.chapter)} / SCIENCE STUDIO</text>
    ${titleLines.slice(0,2).map((line,i)=>`<text x="70" y="${160+i*65}" font-family="Arial,sans-serif" font-size="60" font-weight="700" fill="#173e43">${esc(line)}</text>`).join('')}
    <rect x="60" y="239" width="1378" height="640" rx="34" fill="url(#panel-fill)" stroke="#c9d8cb" stroke-width="2"/>
    ${nested}
    <rect x="1474" y="246" width="382" height="${Math.max(190,metrics.length*86+54)}" rx="30" fill="#214e50"/>
    ${metrics.map((metric,i)=>`<text x="1505" y="${288+i*86}" font-family="Arial,sans-serif" font-size="21" fill="#b4dcd0">${esc(metric.label)}</text><text x="1505" y="${326+i*86}" font-family="Arial,sans-serif" font-size="33" font-weight="700" fill="#fff9e9">${esc(Number.isInteger(metric.value)?metric.value:Number(metric.value.toFixed(2)))} <tspan font-size="20">${esc(metric.unit||'')}</tspan></text>`).join('')}
    <g transform="translate(1663 665)">${scientist(snapshot.progress)}</g>
    <rect x="60" y="1005" width="1796" height="50" rx="16" fill="#e2e9db"/>
    ${intentLines.slice(0,2).map((line,i)=>`<text x="82" y="${intentLines.length>1?1026+i*25:1038}" font-family="Arial,sans-serif" font-size="${intentLines.length>1?21:23}" fill="#294f4d">${esc(line)}</text>`).join('')}
    <path d="M1478 962 H1854" stroke="#c5d1c0" stroke-width="3"/>
    <text x="1483" y="994" font-family="Arial,sans-serif" font-size="20" fill="#526e65">Predict. Try. Observe.</text>
  </svg>`};
}
