// Independent arithmetic fixtures for the pack, separate from common API tests.
import assert from 'node:assert/strict';
import {readFile} from 'node:fs/promises';
import {initialState, validateState, arrival, stateAt, reduce, grade, metrics, feedback, render, sceneIds} from './adapter.mjs';
const lesson = JSON.parse(await readFile(new URL('./lesson.json', import.meta.url)));
const start = initialState(lesson);
const initialCopy = structuredClone(start);
assert.deepEqual(arrival(start), {upperArrival:2, lowerArrival:5, upperPath:3, lowerPath:6, outputArrival:6, critical:'lower'});
const altered = reduce(start, {type:'set', id:'upper', value:7});
assert.deepEqual(start, initialCopy, 'A control action must not mutate the video snapshot.');
assert.equal(arrival(altered).outputArrival, 8);
assert.equal(arrival(altered).critical, 'upper');
const tie = reduce(start, {type:'set', id:'upper', value:5});
assert.equal(arrival(tie).critical, 'both');
assert.equal(arrival(tie).outputArrival, 6);
const noncritical = reduce(start, {type:'set', id:'upper', value:4});
assert.equal(arrival(noncritical).outputArrival, 6);
assert.match(feedback(noncritical,start).text, /stays/);
const slowerFinal = reduce(start, {type:'set', id:'final', value:2.5});
assert.equal(arrival(slowerFinal).outputArrival, 7.5);
assert.equal(arrival(slowerFinal).upperPath, 4.5);
assert.equal(arrival(slowerFinal).lowerPath, 7.5);
const exercise = lesson.exercises[0];
function chosen(upper, lower, final) {
  return {...structuredClone(start),delays:{upper,lower,final}};
}
// Different coordinates in a previous lesson are irrelevant: these are delay values.
for (const values of [[4,3,1],[5,2,1],[3.5,2.5,2.5],[0.6,0.5,0.5]]) {
  assert.equal(grade(chosen(...values),exercise).pass,true,`Expected valid delays ${values}`);
}
for (const values of [[2,5,1],[5,5,1],[5.1,2,1],[2,2,0.5]]) {
  assert.equal(grade(chosen(...values),exercise).pass,false,`Expected invalid exercise result ${values}`);
}
assert.equal(grade(chosen(5+5e-10,2,1),exercise).pass,true,'Only numerical tolerance at budget boundary.');
assert.equal(grade(chosen(5.000001,2,1),exercise).pass,false,'Display rounding cannot hide excess delay.');
assert.equal(arrival(chosen(4+5e-10,4,1)).critical,'both','Near machine precision ties are not unique critical paths.');
assert.equal(arrival(chosen(4.000001,4,1)).critical,'upper');
assert.equal(arrival(chosen(0.5,0.5,0.5)).outputArrival,1);
assert.equal(arrival(chosen(10,10,10)).outputArrival,20);
for (const value of [NaN,Infinity,-1,0,10.01,'2']) {
  assert.throws(()=>reduce(start,{type:'set',id:'upper',value}));
}
assert.throws(()=>reduce(start,{type:'set',id:'unknown',value:2}));
assert.throws(()=>stateAt({sceneId:'missing'},0.4,lesson));
assert.throws(()=>validateState({...start,progress:NaN}));
assert.throws(()=>grade(start,{config:{maximumArrival:6,criticalBranch:'both'}}));
for (const cue of lesson.cues) {
  assert.ok(sceneIds.includes(cue.sceneId));
  for (const progress of [0,0.17,0.325,0.65,1]) {
    const first = stateAt(cue,progress,lesson);
    stateAt(lesson.cues.at(-1),1,lesson);
    assert.deepEqual(stateAt(cue,progress,lesson),first,'Random access must not depend on earlier frames.');
    validateState(first);
    assert.equal(metrics(first).at(-1).value,arrival(first).outputArrival);
    assert.match(render(first,{mode:'film',cue,progress}), /viewBox="0 0 1000 560"/);
    const copied = structuredClone(first);
    copied.delays.upper=0.5;
    assert.deepEqual(stateAt(cue,progress,lesson),first,'Transferred states are independent snapshots.');
  }
}
assert.deepEqual(stateAt(lesson.cues.at(-1),1,lesson).delays,{upper:7,lower:5,final:1});
assert.deepEqual(start,initialCopy);
console.log(JSON.stringify({ok:true,domain:'constant-delay max-plus timing',checks:['independent arrival arithmetic','critical switch and ties','noncritical changes','multiple valid exercise solutions','budget tolerance','invalid input rejection','random access','opaque transferable state']}));
