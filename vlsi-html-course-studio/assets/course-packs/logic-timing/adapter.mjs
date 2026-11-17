// Original two-branch max-plus timing example. Engine-independent ES module.
export const apiVersion = '1.0';
export const sceneIds = ['arrival-paths', 'merge-maximum', 'change-critical'];
const EPSILON = 1e-9;
const LIMITS = {minimum: 0.5, maximum: 10};
const KEYS = ['upper', 'lower', 'final'];
const INITIAL = {upper: 2, lower: 5, final: 1};
const TARGET = {upper: 7, lower: 5, final: 1};
const clone = value => JSON.parse(JSON.stringify(value));
const escape = value => String(value).replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const shown = value => Number(value.toFixed(2)).toString();
const smooth = p => p * p * (3 - 2 * p);

export function validateState(state) {
  if (!state || typeof state !== 'object' || !state.delays || typeof state.delays !== 'object') throw new TypeError('Timing state needs a delays object.');
  for (const key of KEYS) {
    const value = state.delays[key];
    if (typeof value !== 'number' || !Number.isFinite(value) || value < LIMITS.minimum || value > LIMITS.maximum) {
      throw new RangeError(`${key} delay must be a finite number in [0.5, 10] ns.`);
    }
  }
  if (!sceneIds.includes(state.sceneId)) throw new RangeError(`Unsupported timing scene: ${state.sceneId}`);
  if (!Number.isFinite(state.progress) || state.progress < 0 || state.progress > 1) throw new RangeError('Scene progress must be in [0, 1].');
}

export function initialState(course) {
  const delays = clone(course?.modelAssumptions?.initialDelays ?? INITIAL);
  const state = {delays, sceneId: 'arrival-paths', progress: 0};
  validateState(state);
  return state;
}

export function arrival(state) {
  validateState(state);
  const {upper, lower, final} = state.delays;
  const difference = upper - lower;
  return {
    upperArrival: upper, lowerArrival: lower,
    upperPath: upper + final, lowerPath: lower + final,
    outputArrival: Math.max(upper, lower) + final,
    critical: Math.abs(difference) <= EPSILON ? 'both' : difference > 0 ? 'upper' : 'lower',
  };
}

export function stateAt(cue, progress, course) {
  if (!sceneIds.includes(cue?.sceneId)) throw new RangeError(`Unimplemented timing scene: ${cue?.sceneId}`);
  if (!Number.isFinite(progress) || progress < 0 || progress > 1) throw new RangeError('Cue progress must be in [0, 1].');
  const state = initialState(course);
  state.sceneId = cue.sceneId;
  state.progress = progress;
  if (cue.sceneId === 'change-critical') {
    const target = course?.modelAssumptions?.animationTargetDelays ?? TARGET;
    const fraction = smooth(Math.min(progress / 0.65, 1));
    for (const key of KEYS) state.delays[key] += (target[key] - state.delays[key]) * fraction;
  }
  validateState(state);
  return state;
}

export function controls(state) {
  validateState(state);
  return KEYS.map(key => ({id: key, label: `${key === 'final' ? 'Final gate' : key === 'upper' ? 'Upper gate' : 'Lower gate'} delay (ns)`, value: state.delays[key], min: LIMITS.minimum, max: LIMITS.maximum, step: 0.1}));
}

export function reduce(state, action) {
  validateState(state);
  if (action?.type !== 'set' || !KEYS.includes(action.id)) throw new RangeError('Use a set action for upper, lower or final delay.');
  if (typeof action.value !== 'number' || !Number.isFinite(action.value)) throw new TypeError('Gate delay must be a finite number.');
  const result = clone(state);
  result.delays[action.id] = action.value;
  validateState(result);
  return result;
}

export function metrics(state) {
  const result = arrival(state);
  return [
    {id: 'upper-arrival', label: 'Upper input arrival', value: result.upperArrival, unit: 'ns'},
    {id: 'lower-arrival', label: 'Lower input arrival', value: result.lowerArrival, unit: 'ns'},
    {id: 'output-arrival', label: 'Output arrival', value: result.outputArrival, unit: 'ns'},
  ];
}

export function feedback(state, previousState) {
  const result = arrival(state);
  const branch = result.critical === 'both' ? 'Both paths are critical at this tie.' : `The ${result.critical} path is critical.`;
  if (!previousState) return {text: `${branch} Output arrival is max(${shown(result.upperArrival)}, ${shown(result.lowerArrival)}) + ${shown(state.delays.final)} = ${shown(result.outputArrival)} ns.`, tone: 'neutral'};
  const previous = arrival(previousState);
  const delta = result.outputArrival - previous.outputArrival;
  if (Math.abs(delta) <= EPSILON) return {text: `Output arrival stays at ${shown(result.outputArrival)} ns. ${branch} Changing a non-critical branch may leave the output unchanged.`, tone: 'neutral'};
  return {
    text: `Output arrival ${delta < 0 ? 'fell' : 'rose'} by ${shown(Math.abs(delta))} ns. ${branch} This comparison uses the same input arrival and delay model.`,
    tone: delta < 0 ? 'good' : 'warn',
  };
}

export function grade(state, exercise) {
  const result = arrival(state);
  const config = exercise?.config;
  if (!config || !Number.isFinite(config.maximumArrival) || !['upper', 'lower'].includes(config.criticalBranch)) throw new TypeError('Exercise needs a finite maximumArrival and unique upper/lower criticalBranch.');
  const unique = result.critical === config.criticalBranch;
  const within = result.outputArrival <= config.maximumArrival + EPSILON;
  if (unique && within) return {pass: true, feedback: `Valid: the ${config.criticalBranch} path is uniquely critical and output arrival is ${shown(result.outputArrival)} ns, within ${shown(config.maximumArrival)} ns.`};
  const reasons = [];
  if (!unique) reasons.push(result.critical === 'both' ? `The branches tie; make ${config.criticalBranch} uniquely critical.` : `The ${result.critical} path is critical; make ${config.criticalBranch} uniquely critical.`);
  if (!within) reasons.push(`Output arrival exceeds ${shown(config.maximumArrival)} ns. Reduce the longest path delay.`);
  return {pass: false, feedback: reasons.join(' ')};
}

function gate(x, y, title, delay, accent) {
  return `<g><rect x="${x}" y="${y + 5}" width="172" height="90" rx="22" fill="#1c3834" opacity=".08"/><rect x="${x}" y="${y}" width="172" height="90" rx="22" fill="white" stroke="${accent}" stroke-width="3"/><text x="${x + 86}" y="${y + 28}" text-anchor="middle" font-size="18" font-weight="700" fill="#526760">${title}</text><text x="${x + 86}" y="${y + 66}" text-anchor="middle" font-size="31" font-weight="800" fill="#183c36">${escape(shown(delay))}<tspan font-size="19" font-weight="500"> ns</tspan></text></g>`;
}

export function render(state, options = {}) {
  const result = arrival(state);
  const {upper, lower, final} = state.delays;
  const topCritical = result.critical === 'upper' || result.critical === 'both';
  const bottomCritical = result.critical === 'lower' || result.critical === 'both';
  const top = topCritical ? '#d46a4e' : '#a8beb4';
  const bottom = bottomCritical ? '#d46a4e' : '#a8beb4';
  const criticalLabel = result.critical === 'both' ? 'TIE: BOTH PATHS ARE CRITICAL' : `${result.critical.toUpperCase()} PATH IS CRITICAL`;
  const p = state.progress;
  const reveal = state.sceneId === 'arrival-paths' && options.mode !== 'lab' ? Math.min(1, p * 2) : 1;
  const formula = `max(${shown(upper)}, ${shown(lower)}) + ${shown(final)} = ${shown(result.outputArrival)} ns`;
  return `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1000 560" role="img" aria-label="Two reconvergent gate paths. Output arrival is ${escape(formula)}." style="font-family:Arial,Helvetica,sans-serif">
    <rect width="1000" height="560" rx="24" fill="#fffaf0"/>
    <circle cx="938" cy="44" r="116" fill="#f3df98" opacity=".35"/><circle cx="35" cy="523" r="100" fill="#bce0cf" opacity=".3"/>
    <text x="44" y="47" fill="#51756b" font-size="17" font-weight="700" letter-spacing="2">FORK · DELAY · RECONVERGE</text>
    <rect x="615" y="19" width="344" height="42" rx="21" fill="#f9e2d8"/>
    <text x="787" y="46" text-anchor="middle" fill="#a3432d" font-size="16" font-weight="800">${criticalLabel}</text>
    <g fill="none" stroke-linecap="round" stroke-linejoin="round">
      <path d="M 119 265 H 197 Q 218 265 218 244 V 186 Q 218 165 240 165 H 320 M 492 165 H 533 Q 554 165 554 186 V 224 Q 554 245 576 245 H 630" stroke="${top}" stroke-width="${topCritical ? 9 : 6}"/>
      <path d="M 119 265 H 197 Q 218 265 218 286 V 344 Q 218 365 240 365 H 320 M 492 365 H 533 Q 554 365 554 344 V 306 Q 554 285 576 285 H 630" stroke="${bottom}" stroke-width="${bottomCritical ? 9 : 6}"/>
      <path d="M 802 265 H 900" stroke="#d46a4e" stroke-width="9"/>
    </g>
    <circle cx="119" cy="265" r="22" fill="#377d68" stroke="white" stroke-width="6"/>
    <circle cx="900" cy="265" r="17" fill="#d46a4e" stroke="white" stroke-width="5"/>
    <text x="119" y="314" text-anchor="middle" fill="#24473c" font-size="20" font-weight="700">INPUT</text>
    <text x="119" y="342" text-anchor="middle" fill="#637970" font-size="23">0 ns</text>
    ${gate(320, 120, 'UPPER GATE', upper, top)}
    ${gate(320, 320, 'LOWER GATE', lower, bottom)}
    ${gate(630, 220, 'FINAL GATE', final, '#d5a437')}
    <g opacity="${reveal}">
      <text x="539" y="139" text-anchor="middle" font-size="20" font-weight="700" fill="#49645c">${escape(shown(upper))} ns</text>
      <text x="539" y="407" text-anchor="middle" font-size="20" font-weight="700" fill="#49645c">${escape(shown(lower))} ns</text>
      <text x="901" y="205" text-anchor="middle" fill="#a3432d" font-size="33" font-weight="800">${escape(shown(result.outputArrival))}<tspan font-size="19"> ns</tspan></text>
      <text x="901" y="236" text-anchor="middle" fill="#637970" font-size="15" font-weight="700">OUTPUT ARRIVAL</text>
    </g>
    <rect x="145" y="450" width="710" height="75" rx="22" fill="#e5eee4"/>
    <text x="500" y="478" text-anchor="middle" fill="#45665a" font-size="17" font-weight="700">LATEST INPUT ARRIVAL + FINAL GATE DELAY</text>
    <text x="500" y="510" text-anchor="middle" fill="#23493c" font-size="28" font-weight="800">${escape(formula)}</text>
  </svg>`;
}
