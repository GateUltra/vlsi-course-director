import {Board,boardToWorld} from './board.js';
import {crowded,distributed,referenceStarter,referenceTrace,clone,metrics,nets,netBounds,clamp,movable} from './domain.js';
import {mentorFeedback} from './mentor.js';
import {ScientistRig} from './scientist-rig.js';
const labels={starter:'Starting placement',force:'Wirelength pull',quadratic:'Neighbour averaging',spread:'Density spread',reconnect:'Light reconnect'};
const escapeText=s=>String(s).replaceAll('&','&amp;').replaceAll('<','&lt;').replaceAll('>','&gt;');
export function mountLab(element,{onReplay=()=>{}}={}){
 let mode='sandbox',positions=clone(crowded),capacity=2,selectedNet=3,trace=referenceTrace(),index=0,weight=.55,selected=null,before=null,keyBefore=null,keyTimer=null,runTimer=null,feedback=null,fromVideo=false,cueId='overflow';
 element.innerHTML=`<div class="lab-mode-tabs" role="group" aria-label="Choose experiment"><button data-mode="sandbox">01 · Make room</button><button data-mode="hpwl">02 · Measure a net</button><button data-mode="reference">03 · Run the reference</button></div>
 <div class="lab-mode-caption"></div><div class="experiment-layout"><div class="lab-field"><div class="lab-tools" data-controls="sandbox"><button data-preset="crowded">Crowded</button><button data-preset="distributed">Distributed</button><button class="lab-hint">Suggest a move ✦</button></div><div class="lab-tools" data-controls="hpwl"><label>Net <select class="net-select">${nets.map((n,i)=>`<option value="${i}" ${i===3?'selected':''}>${n.join('–')}${n.length===4?' · 4 terminals':''}</option>`).join('')}</select></label><button data-preset="crowded">Reset measurement</button></div><div class="lab-tools reference-tools" data-controls="reference"><button class="ref-reset">Reset</button><button class="ref-back">← Back</button><button class="ref-step">Next phase →</button><button class="ref-run">Run all</button><label>Density weight <input class="density-weight" type="range" min="0" max="2" step=".05" value=".55"><output class="density-value">0.55</output></label></div><div class="reference-phase"></div><div class="lab-board-host"></div><div class="lab-measurement"></div></div>
 <aside class="lab-companion"><div class="companion-portrait"><svg viewBox="0 0 175 175" aria-hidden="true">${ScientistRig({mode:'head',pose:'think'})}</svg><span>YOUR LAB COMPANION</span></div><div class="companion-bubble"><h3></h3><p></p></div><p class="companion-detail"></p><div class="lab-scores"><div><span>EST. WIRELENGTH</span><b class="lab-hpwl"></b><small>HPWL · all six nets</small></div><div><span>OVERFLOW</span><b class="lab-overflow"></b><small>Points beyond capacity</small></div></div><p class="lab-capacity-note"></p><button class="lab-replay">Replay this explanation ↗</button></aside></div>
 <div class="lab-bottom"><p class="lab-instructions"></p><button class="lab-export">Download coordinates ↓</button></div><div class="lab-live sr-only" role="status" aria-live="polite" aria-atomic="true"></div>`;
 const q=s=>element.querySelector(s),host=q('.lab-board-host');
 const nudge=document.createElement('div');nudge.className='lab-nudge';nudge.innerHTML=`<label>Move point <select class="nudge-cell" aria-label="Point to move">${movable.map(id=>`<option>${id}</option>`).join('')}</select></label><div>${[['left','←'],['up','↑'],['down','↓'],['right','→']].map(([direction,arrow])=>`<button data-nudge="${direction}" aria-label="Move selected point ${direction} by a quarter unit">${arrow}</button>`).join('')}</div><span class="nudge-position"></span><small>0.25 units per tap</small>`;host.after(nudge);
 function state(){return {mode,positions:clone(positions),capacity,selectedNet:mode==='hpwl'?selectedNet:null,traceIndex:mode==='reference'?index:null,weight,cueId,metrics:metrics(positions,capacity)}}
 function stop(){clearInterval(runTimer);runTimer=null;clearTimeout(keyTimer);keyTimer=null;keyBefore=null;selected=null;before=null;q('.ref-run').textContent='Run all'}
 function comment(action='observe',previous=null){
  const m=metrics(positions,capacity);
  if(mode==='sandbox'){feedback=mentorFeedback({positions,previous,action});return}
  if(mode==='hpwl'){
   const b=netBounds(selectedNet,positions),old=previous?netBounds(selectedNet,previous):null,d=old?b.hpwl-old.hpwl:null;
   feedback={tone:old&&d<-.00001?'success':'thoughtful',title:old?(Math.abs(d)<.00001?'The box did not change.':d<0?'A smaller bounding box.':'A larger bounding box.'):'Measure the box, not the line.',lines:[`Width ${b.width.toFixed(2)} + height ${b.height.toFixed(2)}.`,`This net: ${b.hpwl.toFixed(2)}; all nets: ${m.hpwl.toFixed(2)}.`],hint:Math.abs(d??1)<.00001?'A terminal can move inside a net’s bounding box without changing its extreme coordinates. HPWL then stays the same.':'Try moving B, C, E or F. The highlighted rectangle spans the selected net’s extreme x and y coordinates. HPWL is an estimate, not a routed path.'};return;
  }
  const step=trace[index],phase=fromVideo?'Video snapshot':labels[step.phase];
  let detail=step.phase==='starter'?'The reference begins with 6 force updates, then 3 neighbour-averaging updates.':step.phase==='force'?'Connected neighbours pull movable points closer. A and D stay fixed.':step.phase==='quadratic'?'The update averages neighbours in sequence; it is a small teaching heuristic.':step.phase==='spread'?'Points in an overfull region move away from its centre. The capacity score may temporarily get worse.':'One light reconnect follows this spread. The loop repeats 12 times.';
  if(index===trace.length-1&&!fromVideo)detail=`Completed 12 spread–reconnect rounds at weight ${weight.toFixed(2)}. Compare this measured result with the default 48.12 and overflow 2; a larger weight need not improve either score.`;
  feedback={tone:m.overflow===2?'thoughtful':'warning',title:phase+'. Read both scores.',lines:[`HPWL ${m.hpwl.toFixed(2)} · overflow ${m.overflow}.`,'Six points. Four available places.'],hint:detail+' With capacity 1 in each of 4 regions, total overflow cannot fall below 2. This point model does not certify cell legalization.'};
 }
 function announce(){q('.lab-live').textContent=[feedback.title,...feedback.lines,feedback.hint].join(' ')}
 function draw(){
  const focus=host.contains(document.activeElement)?document.activeElement.closest('[data-cell]')?.dataset.cell:null,m=metrics(positions,capacity),moving=!!(selected||keyBefore);
  const visible=moving?{title:'Try a move. Watch the box.',lines:['The scores update as you move.','I’ll compare when you finish.'],hint:'A and D stay fixed.',tone:'neutral'}:feedback;
  host.innerHTML=Board({positions,capacity,selectedNet:mode==='hpwl'?selectedNet:null,interactive:mode!=='reference',highlightBin:moving?null:feedback.highlightBin,suggestedCell:moving?null:feedback.suggestedCell,arrows:mode==='reference'&&!fromVideo?trace[index].arrows:[],uid:'lab'});
  if(focus)host.querySelector(`[data-cell="${focus}"]`)?.focus({preventScroll:true});
  q('.companion-bubble h3').textContent=visible.title;q('.companion-bubble p').textContent=visible.lines.join(' ');q('.companion-detail').textContent=visible.hint;q('.companion-bubble').dataset.tone=visible.tone;
  q('.lab-hpwl').textContent=m.hpwl.toFixed(2);q('.lab-overflow').textContent=m.overflow;q('.lab-overflow').dataset.good=m.overflow===0;
  q('.lab-capacity-note').textContent=`${capacity} point${capacity===1?'':'s'} per region · A and D fixed. ${mode==='reference'?'Course reference, capacity 1.':'Designed teaching comparison, capacity 2.'}`;
  q('.lab-mode-caption').textContent=mode==='reference'?'COURSE REFERENCE · Exact algorithm updates, original capacity 1':mode==='hpwl'?'BOUNDING-BOX EXPERIMENT · Select a net, move a point, compare':'DESIGNED COMPARISON · Make room without ignoring the wires';
  q('.lab-instructions').textContent=mode==='reference'?'Step through the actual update order. Changing density weight resets the run. Coordinates are not clamped by the reference algorithm.':'Drag B, C, E or F, or focus a point and use the arrow keys (0.1 units). A and D are fixed. More than one layout can meet the capacity requirement.';
  q('.reference-phase').hidden=mode!=='reference';q('.reference-phase').textContent=`${fromVideo?'Transferred video state':`${index+1} / ${trace.length} · ${labels[trace[index].phase]}`} ${trace[index].iteration?`· iteration ${trace[index].iteration}`:''}`;
  q('.lab-measurement').textContent=mode==='hpwl'?`Selected net ${nets[selectedNet].join('–')}: ${netBounds(selectedNet,positions).hpwl.toFixed(2)} coordinate units. All six nets total ${m.hpwl.toFixed(2)}.`:'';
  nudge.hidden=mode==='reference';const chosen=positions[q('.nudge-cell').value];q('.nudge-position').textContent=`(${chosen.x.toFixed(2)}, ${chosen.y.toFixed(2)})`;
  element.querySelectorAll('[data-controls]').forEach(n=>n.hidden=n.dataset.controls!==mode);
  element.querySelectorAll('[data-mode]').forEach(n=>{n.setAttribute('aria-pressed',n.dataset.mode===mode);n.classList.toggle('active',n.dataset.mode===mode)});
  q('.ref-back').disabled=index===0;q('.ref-step').disabled=index===trace.length-1;
  element.labState=state();element.mentorState=clone(feedback);
 }
 function resetMode(next){stop();mode=next;capacity=mode==='reference'?1:2;positions=clone(mode==='reference'?referenceStarter:crowded);index=0;fromVideo=false;cueId=mode==='reference'?'algorithm_map':mode==='hpwl'?'hpwl_measure':'overflow';comment();draw();announce()}
 function useReference(i){index=clamp(i,0,trace.length-1);positions=clone(trace[index].positions);fromVideo=false;comment();draw();announce()}
 element.querySelectorAll('[data-mode]').forEach(b=>b.onclick=()=>resetMode(b.dataset.mode));
 element.querySelectorAll('[data-preset]').forEach(b=>b.onclick=()=>{stop();positions=clone(b.dataset.preset==='distributed'?distributed:crowded);fromVideo=false;comment('preset');draw();announce()});
 q('.lab-hint').onclick=()=>{stop();comment('hint');draw();announce()};
 q('.nudge-cell').onchange=draw;
 nudge.querySelectorAll('[data-nudge]').forEach(b=>b.onclick=()=>{if(mode==='reference')return;stop();const previous=clone(positions),id=q('.nudge-cell').value,d={left:[-.25,0],right:[.25,0],up:[0,.25],down:[0,-.25]}[b.dataset.nudge];positions[id]={x:clamp(positions[id].x+d[0],0,8),y:clamp(positions[id].y+d[1],0,8)};comment('key',previous);draw();announce()});
 q('.net-select').onchange=e=>{selectedNet=+e.target.value;comment();draw();announce()};
 q('.ref-reset').onclick=()=>{stop();useReference(0)};
 q('.ref-back').onclick=()=>{stop();useReference(index-1)};q('.ref-step').onclick=()=>{stop();useReference(index+1)};
 q('.ref-run').onclick=()=>{if(runTimer){stop();return}if(index===trace.length-1)useReference(0);q('.ref-run').textContent='Pause';runTimer=setInterval(()=>{if(index>=trace.length-1){stop();return}useReference(index+1)},650)};
 q('.density-weight').oninput=e=>{stop();weight=+e.target.value;q('.density-value').textContent=weight.toFixed(2);trace=referenceTrace(weight);useReference(0)};
 function pointer(e){const p=new DOMPoint(e.clientX,e.clientY).matrixTransform(host.querySelector('svg').getScreenCTM().inverse());return boardToWorld(p,positions)}
 host.addEventListener('pointerdown',e=>{if(mode==='reference')return;const id=e.target.closest('[data-cell]')?.dataset.cell;if(!movable.includes(id))return;stop();selected=id;before=clone(positions);host.setPointerCapture(e.pointerId);e.preventDefault()});
 host.addEventListener('pointermove',e=>{if(!selected)return;positions[selected]=pointer(e);draw()});
 function end(){if(!selected)return;const id=selected;selected=null;comment('drag',before);before=null;draw();announce();host.querySelector(`[data-cell="${id}"]`)?.focus({preventScroll:true})}
 host.addEventListener('pointerup',end);host.addEventListener('pointercancel',end);host.addEventListener('lostpointercapture',end);
 host.addEventListener('keydown',e=>{if(mode==='reference')return;const id=e.target.closest('[data-cell]')?.dataset.cell,d={ArrowLeft:[-.1,0],ArrowRight:[.1,0],ArrowUp:[0,.1],ArrowDown:[0,-.1]}[e.key];if(!movable.includes(id)||!d)return;e.preventDefault();if(!keyBefore)keyBefore=clone(positions);clearTimeout(keyTimer);positions[id]={x:clamp(positions[id].x+d[0],0,8),y:clamp(positions[id].y+d[1],0,8)};draw();keyTimer=setTimeout(()=>{comment('key',keyBefore);keyBefore=null;draw();announce()},280)});
 q('.lab-replay').onclick=()=>onReplay(cueId);
 q('.lab-export').onclick=()=>{const blob=new Blob([JSON.stringify({...state(),source:'Placement Lesson 06 experiment',fixed:['A','D']},null,2)],{type:'application/json'}),url=URL.createObjectURL(blob),a=document.createElement('a');a.href=url;a.download='placement-experiment.json';a.click();setTimeout(()=>URL.revokeObjectURL(url),1000)};
 comment();draw();
 return {getState:state,takeState(incoming){stop();mode=incoming.mode|| (incoming.capacity===1?'reference':'sandbox');if(!['sandbox','reference','hpwl'].includes(mode))mode='sandbox';capacity=mode==='reference'?1:2;positions=clone(incoming.positions||crowded);cueId=incoming.cueId||incoming.id||cueId;if(Number.isInteger(incoming.selectedNet)){selectedNet=incoming.selectedNet;q('.net-select').value=selectedNet}if(mode==='reference'){weight=Number.isFinite(incoming.weight)?clamp(incoming.weight,0,2):.55;trace=referenceTrace(weight);q('.density-weight').value=weight;q('.density-value').textContent=weight.toFixed(2);index=Number.isInteger(incoming.traceIndex)?clamp(incoming.traceIndex,0,trace.length-1):trace.reduce((best,t,i)=>{const distance=s=>Object.keys(positions).reduce((n,id)=>n+(positions[id].x-s.positions[id].x)**2+(positions[id].y-s.positions[id].y)**2,0);return distance(t)<distance(trace[best])?i:best},0)}fromVideo=Number.isFinite(incoming.t)||incoming.source==='video';comment(fromVideo?'transfer':'preset');draw();announce();element.scrollIntoView({behavior:matchMedia('(prefers-reduced-motion:reduce)').matches?'instant':'smooth',block:'start'})},destroy:stop};
}



