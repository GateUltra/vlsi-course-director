import {crowded,distributed,referenceStarter,referenceTrace,clone,clamp,smooth,interpolatePositions} from './domain.js';
const defaultTrace=referenceTrace(.55);
const byWeight=new Map([[.55,defaultTrace]]);
export function traceFor(weight=.55){if(!byWeight.has(weight))byWeight.set(weight,referenceTrace(weight));return byWeight.get(weight)}
function travel(trace,from,to,p){
 const index=from+(to-from)*smooth(clamp(p)),i=Math.floor(index),j=Math.min(trace.length-1,i+1),f=index-i;
 return {positions:interpolatePositions(trace[i].positions,trace[j].positions,f),traceIndex:i,phase:trace[j].phase,iteration:trace[j].iteration,arrows:trace[j].arrows};
}
/** One semantic state contract for film rendering, voice switching and lab transfer. */
export function stateAt(t,clock,script={}){
 const segments=clock.segments||clock.cues||[];
 if(!segments.length)throw new Error('Measured cue clock is missing.');
 const cue=segments.find((s,i)=>t>=(i?s.start:0)&&t<(s.sceneEnd??segments[i+1]?.start??clock.duration))||segments.at(-1);
 const meta=(script.cues||[]).find(c=>c.id===cue.id)||cue;
 const sceneEnd=cue.sceneEnd??segments[segments.indexOf(cue)+1]?.start??clock.duration;
 const progress=clamp((t-cue.start)/Math.max(.001,sceneEnd-cue.start));
 const state={t,duration:clock.duration,cueId:cue.id,cueAge:Math.max(0,t-cue.start),progress,chapter:meta.chapter||cue.chapter,title:meta.title||cue.title,layout:meta.layout||cue.id,positions:clone(crowded),capacity:2,mode:'sandbox',selectedNet:null,showDensity:0,traceIndex:null,weight:.55,phase:'starter',iteration:0,arrows:[],trace:defaultTrace};
 const id=state.cueId;
 if(['welcome','city','flow'].includes(id))state.positions=clone(distributed);
 if(id==='temptation')state.positions=interpolatePositions(distributed,crowded,smooth(progress/.65));
 if(['nets','hpwl_multi','hpwl_inside'].includes(id))state.selectedNet=4;
 if(['hpwl_box','hpwl_measure','hpwl_limit'].includes(id))state.selectedNet=3;
 if(id.startsWith('hpwl_'))state.mode='hpwl';
 if(id==='hpwl_inside')state.positions.B={x:1+4*smooth(progress/.75),y:1+2*smooth(progress/.75)};
 if(['bins','capacity','overflow','predict','spread_demo','tradeoff'].includes(id))state.showDensity=id==='bins'?smooth(progress/.5):1;
 if(id==='spread_demo')state.positions=interpolatePositions(crowded,distributed,smooth(progress/.27));
 if(['tradeoff','challenge','takeaway','ending'].includes(id)){state.positions=clone(distributed);state.showDensity=1}
 const refIds=['reference_start','algorithm_map','force','quadratic','density_push','reconnect','repeat','heuristic','results','capacity_bound','diagnosis','fair_compare','weight','lab_transfer','lab_reference'];
 if(refIds.includes(id)){
  state.mode='reference';state.capacity=1;state.showDensity=1;state.positions=clone(referenceStarter);state.traceIndex=0;
  if(id==='force')Object.assign(state,travel(defaultTrace,0,6,progress/.7));
  if(id==='quadratic')Object.assign(state,travel(defaultTrace,6,9,progress/.7));
  if(id==='density_push')Object.assign(state,travel(defaultTrace,9,10,progress/.65),{phase:'spread',iteration:1,arrows:defaultTrace[10].arrows});
  if(id==='reconnect')Object.assign(state,travel(defaultTrace,10,11,progress/.65),{phase:'reconnect',iteration:1,arrows:defaultTrace[11].arrows});
  if(id==='repeat')Object.assign(state,travel(defaultTrace,11,33,progress/.82));
  if(['heuristic','results','capacity_bound','diagnosis','fair_compare','lab_transfer'].includes(id)){Object.assign(state,{positions:clone(defaultTrace.at(-1).positions),traceIndex:33,phase:'reconnect',iteration:12})}
  if(id==='weight'){
   const weight=[0,.55,1,2][Math.min(3,Math.floor(progress*4))],trace=traceFor(weight);
   Object.assign(state,{weight,trace,positions:clone(trace.at(-1).positions),traceIndex:33,phase:'reconnect',iteration:12});
  }
  if(id==='lab_reference')Object.assign(state,travel(defaultTrace,0,11,progress/.8));
 }
 if(id==='lab_predict'){state.showDensity=1;const target=clone(crowded);target.B={x:6,y:2};state.positions=interpolatePositions(crowded,target,smooth((progress-.2)/.5))}
 return state;
}
