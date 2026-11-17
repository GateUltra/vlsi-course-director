// Mechanical runtime regression; scientific expectations live in each pack/check.mjs.
import assert from 'node:assert/strict';
import {readFile} from 'node:fs/promises';
import {resolve} from 'node:path';
import {pathToFileURL} from 'node:url';
import * as core from './core.mjs';
import {sceneAt} from './scene.mjs';
if(!process.argv[2])throw new Error('Usage: node check_core.mjs PATH_TO_COURSE_PACK');
const root=resolve(process.argv[2]);
const course=JSON.parse(await readFile(resolve(root,'lesson.json'),'utf8'));
const adapter=await import(pathToFileURL(resolve(root,course.adapter)).href);
core.validateAdapter(course,adapter);
const clock={id:'test',duration:course.cues.length*10+1,segments:course.cues.map((cue,i)=>({id:cue.id,start:.3+i*10,end:9+i*10,sceneEnd:10.3+i*10}))};
core.validateClock(course,clock);
for(const [index,cue] of course.cues.entries())for(const progress of [0,.17,.5,.99]) {
  const time=clock.segments[index].start+progress*10;
  const expected=core.snapshotAt(time,clock,course,adapter);
  core.snapshotAt(1,clock,course,adapter);
  assert.deepEqual(core.snapshotAt(time,clock,course,adapter),expected);
  assert.deepEqual(core.importSnapshot(expected,course,adapter),expected);
  assert.ok(Math.abs(core.semanticTime(core.semanticPosition(time,clock),clock)-time)<1e-8);
  assert.match(sceneAt(time,clock,course,adapter).svg,/<svg[^>]*viewBox="0 0 1920 1080"/);
}
for(const time of [0,.2,clock.duration-.1,clock.duration])assert.ok(Math.abs(core.semanticTime(core.semanticPosition(time,clock),clock)-time)<1e-8);
const snapshot=core.snapshotAt(2,clock,course,adapter);
assert.throws(()=>core.importSnapshot({...snapshot,courseVersion:'wrong'},course,adapter));
assert.throws(()=>core.importSnapshot({...snapshot,cueId:'unknown'},course,adapter));
assert.throws(()=>core.importSnapshot({...snapshot,progress:NaN},course,adapter));
assert.throws(()=>core.validateClock(course,{...clock,provisional:true}));
assert.throws(()=>core.validateClock(course,{...clock,segments:clock.segments.slice(1)}));
const badScene=structuredClone(course);badScene.cues[0].sceneId='unimplemented';
assert.throws(()=>core.validateAdapter(badScene,adapter));
console.log(JSON.stringify({passed:true,course:course.id,engine:core.ENGINE_VERSION,checks:['scene coverage','complete measured clocks','random access','semantic intro/cue/tail mapping','opaque snapshot transfer','course/version isolation','frame composition']}));
