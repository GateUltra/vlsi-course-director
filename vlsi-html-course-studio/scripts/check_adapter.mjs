import assert from 'node:assert/strict';
import {readFile} from 'node:fs/promises';
import {resolve, dirname} from 'node:path';
import {pathToFileURL, fileURLToPath} from 'node:url';

const root = resolve(process.argv[2] ?? '.');
const course = JSON.parse(await readFile(resolve(root, 'lesson.json'), 'utf8'));
const adapter = await import(pathToFileURL(resolve(root, course.adapter)));
const clone = value => structuredClone(value);
const freeze = value => { if (value && typeof value === 'object') { Object.freeze(value); Object.values(value).forEach(freeze); } return value; };
const jsonState = value => {
  function visit(item) {
    assert.notEqual(item, undefined, 'State must not contain undefined');
    assert.notEqual(typeof item, 'function', 'State must be JSON');
    if (typeof item === 'number') assert.ok(Number.isFinite(item));
    if (item && typeof item === 'object') Object.values(item).forEach(visit);
  }
  visit(value); assert.deepEqual(JSON.parse(JSON.stringify(value)), value); adapter.validateState(value);
};
assert.equal(adapter.apiVersion, '1.0');
for (const key of ['initialState','validateState','stateAt','render','controls','reduce','metrics','feedback','grade']) assert.equal(typeof adapter[key], 'function', `Missing adapter ${key}`);
assert.ok(Array.isArray(adapter.sceneIds) && adapter.sceneIds.length);
assert.equal(new Set(adapter.sceneIds).size, adapter.sceneIds.length);
for (const cue of course.cues) assert.ok(adapter.sceneIds.includes(cue.sceneId), `Unimplemented scene ${cue.sceneId}`);
freeze(course);
const initial = adapter.initialState(course); jsonState(initial);
const states = [initial];
for (const cue of course.cues) {
  for (const progress of [0, .371, 1]) {
    const state = adapter.stateAt(cue, progress, course); jsonState(state);
    const frozen = freeze(clone(state));
    const visual = adapter.render(frozen, {mode:'film', cue, progress});
    assert.equal(typeof visual, 'string');
    assert.match(visual, /<svg\b/); assert.match(visual, /viewBox=["']0 0 1000 560["']/);
    adapter.stateAt(course.cues.at(-1), .819, course);
    assert.deepEqual(adapter.stateAt(cue, progress, course), state, 'Random-access state differs');
    assert.equal(adapter.render(frozen,{mode:'film',cue,progress}),visual,'Render must be deterministic');
    states.push(state);
  }
}
for (const state of states) {
  const frozen = freeze(clone(state));
  const metrics = adapter.metrics(frozen);
  assert.ok(Array.isArray(metrics) && metrics.length);
  assert.equal(new Set(metrics.map(m=>m.id)).size, metrics.length);
  for (const metric of metrics) { assert.equal(typeof metric.label,'string'); assert.ok(Number.isFinite(metric.value)); }
  const controls = adapter.controls(frozen); assert.ok(Array.isArray(controls));
  assert.equal(new Set(controls.map(c=>c.id)).size, controls.length);
  for (const control of controls) {
    assert.equal(typeof control.id,'string'); assert.equal(typeof control.label,'string');
    for (const key of ['value','min','max','step']) assert.ok(Number.isFinite(control[key]));
    assert.ok(control.min<=control.value && control.value<=control.max && control.step>0);
    for (const value of [control.min,control.value,control.max]) {
      const next=adapter.reduce(frozen,{type:'set',id:control.id,value}); jsonState(next);
      assert.deepEqual(adapter.controls(next).map(c=>c.id).sort(),controls.map(c=>c.id).sort(),'Control IDs must remain stable during interaction');
    }
  }
  const feedback=adapter.feedback(frozen,freeze(clone(initial)));
  assert.equal(typeof feedback.text,'string'); assert.ok(['neutral','good','warn'].includes(feedback.tone));
  for (const exercise of course.exercises) { const grade=adapter.grade(frozen,exercise); assert.equal(typeof grade.pass,'boolean');assert.equal(typeof grade.feedback,'string'); }
  if (adapter.pointerAction) {
    const action=adapter.pointerAction(frozen,{x:.4,y:.6});
    if (action!==null) jsonState(adapter.reduce(frozen,action));
  }
}
const runtimeURL=pathToFileURL(resolve(dirname(fileURLToPath(import.meta.url)),'../assets/runtime/core.mjs'));
const runtime=await import(runtimeURL);
runtime.validateAdapter(course,adapter);
const duration=course.cues.length*2;
const clock={id:course.defaultVoice,duration,segments:course.cues.map((c,i)=>({id:c.id,start:i*2,end:i*2+1.5,sceneEnd:(i+1)*2}))};
runtime.validateClock(course,clock);
for (const t of [0,.719,duration/2,duration]) {
  const snapshot=runtime.snapshotAt(t,clock,course,adapter);
  const restored=runtime.importSnapshot(clone(snapshot),course,adapter);
  assert.ok(restored, 'Snapshot import must return state or snapshot');
  const wrong=clone(snapshot);wrong.courseVersion='0.0.0';assert.throws(()=>runtime.importSnapshot(wrong,course,adapter));
}
console.log(JSON.stringify({passed:true,cues:course.cues.length,states:states.length,checks:['scene coverage','immutable inputs','random access','serializable valid state','control endpoints','metric/grade contracts','snapshot compatibility']}));
