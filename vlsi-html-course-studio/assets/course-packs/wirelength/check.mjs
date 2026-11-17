import assert from 'node:assert/strict';
import {readFile} from 'node:fs/promises';
import * as adapter from './adapter.mjs';
const course=JSON.parse(await readFile(new URL('./lesson.json',import.meta.url),'utf8'));
const original=adapter.initialState(course);
assert.equal(adapter.metrics(original)[2].value,11);
const moved=adapter.reduce(original,{type:'move',x:5,y:4});
assert.equal(adapter.metrics(moved)[2].value,5);
assert.deepEqual(original.b,{x:8,y:7});
const exercise=course.exercises[0];
for(const b of [{x:5,y:4},{x:2,y:6},{x:8,y:2},{x:0,y:4}])assert.equal(adapter.grade({...original,b},exercise).pass,true);
for(const b of [{x:2,y:2},{x:9,y:9},{x:8.000001,y:2}])assert.equal(adapter.grade({...original,b},exercise).pass,false);
assert.equal(adapter.grade({...original,b:{x:8+8e-15,y:2}},exercise).pass,true);
assert.throws(()=>adapter.validateState({...original,a:{x:3,y:2}}));
assert.throws(()=>adapter.stateAt({sceneId:'missing'},.5));
assert.throws(()=>adapter.reduce(original,{type:'set',id:'bx',value:NaN}));
for(const cue of course.cues)for(const progress of [0,.17,.51,1]){
 const first=adapter.stateAt(cue,progress,course);adapter.stateAt(course.cues.at(-1),.99,course);
 assert.deepEqual(adapter.stateAt(cue,progress,course),first);adapter.validateState(first);assert.match(adapter.render(first),/<svg/);
}
assert.equal(adapter.metrics(adapter.stateAt(course.cues[2],1))[2].value,5);
console.log(JSON.stringify({passed:true,course:course.id,checks:['independent metric expectations','fixed pin','multiple valid solutions','strict exercise bounds','deterministic scenes','unknown scene refusal']}));
