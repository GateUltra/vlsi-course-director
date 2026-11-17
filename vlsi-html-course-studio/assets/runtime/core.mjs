// The runtime never inspects a domain-specific state field.
export const ENGINE_VERSION = '2.0.0';
export const CONTRACT_VERSION = '1.0';
export const copy = value => structuredClone(value);
export const clamp = (value, lo = 0, hi = 1) => Math.max(lo, Math.min(hi, value));
export const escapeText = value => String(value).replace(/[&<>"']/g, char => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[char]));
const fail = message => { throw new Error(message); };
export function assertJson(value, path = 'state') {
  if (value === null || typeof value === 'string' || typeof value === 'boolean') return;
  if (typeof value === 'number' && Number.isFinite(value)) return;
  if (Array.isArray(value)) { value.forEach((v, i) => assertJson(v, `${path}[${i}]`)); return; }
  if (typeof value === 'object' && Object.getPrototypeOf(value) === Object.prototype) {
    Object.entries(value).forEach(([key, v]) => assertJson(v, `${path}.${key}`)); return;
  }
  fail(`Non-JSON or nonfinite value at ${path}`);
}
export function validateAdapter(course, adapter) {
  if (course.contractVersion !== CONTRACT_VERSION || adapter.apiVersion !== CONTRACT_VERSION) fail('Unsupported course/adapter contract version');
  for (const name of ['initialState','validateState','stateAt','render','controls','reduce','metrics','feedback','grade']) {
    if (typeof adapter[name] !== 'function') fail(`Adapter missing ${name}`);
  }
  if (!Array.isArray(adapter.sceneIds) || new Set(adapter.sceneIds).size !== adapter.sceneIds.length) fail('Adapter sceneIds must be unique');
  for (const cue of course.cues) if (!adapter.sceneIds.includes(cue.sceneId)) fail(`Unimplemented scene ${cue.sceneId} for cue ${cue.id}`);
  const state = adapter.initialState(course); assertJson(state); adapter.validateState(state);
  return true;
}
export function validateClock(course, clock) {
  if (!Number.isFinite(clock.duration) || clock.duration <= 0 || clock.provisional) fail('A measured positive clock is required');
  if (!Array.isArray(clock.segments) || clock.segments.length !== course.cues.length) fail('Clock must cover every cue exactly');
  let previous = null;
  clock.segments.forEach((segment, i) => {
    if (segment.id !== course.cues[i].id) fail('Clock and lesson cue order differ');
    const {start, end, sceneEnd} = segment;
    if (![start,end,sceneEnd].every(Number.isFinite) || !(0 <= start && start < end && end <= sceneEnd && sceneEnd <= clock.duration)) fail(`Invalid interval for ${segment.id}`);
    if (previous !== null && Math.abs(start - previous) > 1e-6) fail(`Clock gap/overlap at ${segment.id}`);
    previous = sceneEnd;
  });
  return true;
}
export function semanticPosition(time, clock) {
  if (!Number.isFinite(time)) fail('Time must be finite');
  const first = clock.segments[0], last = clock.segments.at(-1);
  if (time < first.start) return {cueId:first.id,progress:0,region:'intro',regionProgress:clamp(time / (first.start || 1))};
  if (time >= last.sceneEnd) return {cueId:last.id,progress:1,region:'tail',regionProgress:clamp((time-last.sceneEnd)/(clock.duration-last.sceneEnd || 1))};
  const cue = clock.segments.find(segment => time < segment.sceneEnd);
  return {cueId:cue.id,progress:clamp((time-cue.start)/(cue.sceneEnd-cue.start)),region:'cue'};
}
export function semanticTime(position, clock) {
  const cue = clock.segments.find(segment => segment.id === position.cueId);
  if (!cue) fail(`Unknown cue ${position.cueId}`);
  if (position.region === 'intro') return clamp(position.regionProgress) * clock.segments[0].start;
  if (position.region === 'tail') return clock.segments.at(-1).sceneEnd + clamp(position.regionProgress)*(clock.duration-clock.segments.at(-1).sceneEnd);
  return cue.start + clamp(position.progress)*(cue.sceneEnd-cue.start);
}
export function snapshotAt(time, clock, course, adapter) {
  const position = semanticPosition(time, clock);
  const cue = course.cues.find(item => item.id === position.cueId);
  if (!cue || !adapter.sceneIds.includes(cue.sceneId)) fail('Missing cue or scene implementation');
  const state = adapter.stateAt(copy(cue), position.progress, course);
  assertJson(state); adapter.validateState(state);
  return {contractVersion:CONTRACT_VERSION,courseId:course.id,courseVersion:course.version,cueId:cue.id,progress:position.progress,state:copy(state)};
}
export function importSnapshot(snapshot, course, adapter) {
  assertJson(snapshot);
  if (snapshot.contractVersion !== CONTRACT_VERSION || snapshot.courseId !== course.id || snapshot.courseVersion !== course.version) fail('Snapshot belongs to a different course or version');
  if (!course.cues.some(cue => cue.id === snapshot.cueId) || !Number.isFinite(snapshot.progress) || snapshot.progress < 0 || snapshot.progress > 1) fail('Invalid snapshot cue or progress');
  adapter.validateState(snapshot.state);
  return copy(snapshot);
}
export async function loadStudio() {
  const read = async path => { const response = await fetch(path); if (!response.ok) fail(`Cannot load ${path}: HTTP ${response.status}`); return response.json(); };
  const [course, manifest] = await Promise.all([read('./pack/lesson.json'),read('./media/manifest.json')]);
  const base = new URL('./pack/', location.href);
  const adapterURL = new URL(course.adapter, base);
  if (!adapterURL.href.startsWith(base.href)) fail('Adapter escapes course pack');
  const adapter = await import(adapterURL.href);
  validateAdapter(course, adapter);
  if (typeof manifest.buildIdentity !== 'string' || !manifest.buildIdentity) fail('Missing build identity');
  if (!Array.isArray(manifest.tracks) || !manifest.tracks.length) fail('Missing media tracks');
  const clocks = new Map();
  await Promise.all(manifest.tracks.map(async track => {
    const clock = await read(track.timing); validateClock(course, clock);
    if (clock.buildIdentity !== manifest.buildIdentity || clock.id !== track.id) fail('Clock build identity does not match media');
    clocks.set(track.id, clock);
  }));
  return {course,manifest,adapter,clocks};
}
