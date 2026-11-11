import {clone,metrics} from './domain.js';

// A local, deterministic teaching companion. Every judgement uses the same
// geometry and capacity rule as the picture; no text is sent to a service.
const capacity=2;
const movable=['B','C','E','F'];
const bins=['lower-left','lower-right','upper-left','upper-right'];
const centres=[{x:2,y:2},{x:6,y:2},{x:2,y:6},{x:6,y:6}];
const binOf=p=>(p.y>=4?2:0)+(p.x>=4?1:0);
const f=n=>n.toFixed(1);
const capital=s=>s[0].toUpperCase()+s.slice(1);
const near=(a,b)=>Math.abs(a-b)<1e-7;
const targetOffsets=[[0,0],[-1,0],[1,0],[0,-1],[0,1]];

function freeTarget(positions,cell,toBin){
  // Prefer the centre, but leave enough separation to see and grab both cells.
  // Every offset is strictly inside its bin, away from the dividing boundary.
  const centre=centres[toBin];
  return targetOffsets.map(([dx,dy])=>({x:centre.x+dx,y:centre.y+dy}))
    .find(target=>Object.entries(positions).every(([id,p])=>id===cell||Math.hypot(p.x-target.x,p.y-target.y)>=.75))||null;
}

function recommendation(positions,m){
  // Offer one possible experiment, not a claim of globally optimal placement.
  // Test the exact target before recommending it, including fixed A and D.
  const candidates=[];
  for(const cell of movable){
    const fromBin=binOf(positions[cell]);
    if(m.counts[fromBin]<=capacity)continue;
    for(let toBin=0;toBin<bins.length;toBin++){
      if(toBin===fromBin||m.counts[toBin]>=capacity)continue;
      const target=freeTarget(positions,cell,toBin);
      if(!target)continue;
      const targetOffset=target.x!==centres[toBin].x||target.y!==centres[toBin].y;
      const p=clone(positions);p[cell]=target;
      const result=metrics(p);
      if(result.overflow<m.overflow)candidates.push({cell,fromBin,toBin,target,targetOffset,result,
        overflowReduction:m.overflow-result.overflow,hpwlDelta:result.hpwl-m.hpwl});
    }
  }
  candidates.sort((a,b)=>b.overflowReduction-a.overflowReduction||a.result.hpwl-b.result.hpwl||movable.indexOf(a.cell)-movable.indexOf(b.cell)||a.toBin-b.toBin);
  return candidates[0]||null;
}

/**
 * action: initial | transfer | preset | drag | key | blend | replay | hint.
 * `previous` is the full layout BEFORE the gesture, not the last pointer event.
 * Return plain text; the view must escape it when embedding it in SVG/HTML.
 * Feedback is advisory: it never changes a cell or starts speech automatically.
 */
export function mentorFeedback({positions,previous=null,action='initial',cell=null}={}){
  const m=metrics(positions),before=previous?metrics(previous):null;
  const delta=before?{overflow:m.overflow-before.overflow,hpwl:m.hpwl-before.hpwl}:null;
  const suggestion=recommendation(positions,m);
  const crowdedBin=m.counts.indexOf(Math.max(...m.counts));
  const countLine=`${capital(bins[crowdedBin])}: ${m.counts[crowdedBin]} points, 2 places.`;
  const wireLine=before?`HPWL ${f(before.hpwl)} → ${f(m.hpwl)}.`:`HPWL is ${f(m.hpwl)}.`;
  const overflowLine=before?`Overflow ${before.overflow} → ${m.overflow}.`:`Overflow is ${m.overflow}.`;
  const suggestionText=suggestion
    ?`Try moving ${suggestion.cell} from the ${bins[suggestion.fromBin]} region towards ${suggestion.targetOffset?'a free place near the centre':'the centre'} of the ${bins[suggestion.toBin]} region. At (${suggestion.target.x}, ${suggestion.target.y}), overflow would be ${suggestion.result.overflow} and HPWL would be ${f(suggestion.result.hpwl)}. This is one possible move, not an optimum.`
    :'Try shortening a connection while keeping every region at two points or fewer. A and D stay fixed.';
  const context=action==='transfer'?"This is the exact layout you paused in the film. ":'';
  const result=(id,tone,title,lines,detail='')=>({id,tone,title,lines,
    hint:context+(detail?`${detail} `:'')+suggestionText,
    highlightBin:m.overflow>0?crowdedBin:null,
    suggestedCell:suggestion?.cell||null,suggestion,metrics:m,delta,action,cell});

  if(action==='hint'){
    if(suggestion)return result('suggest-move','thoughtful','One small experiment.',[
      `Try ${suggestion.cell} in the ${bins[suggestion.toBin]} region.`,
      `Overflow would fall to ${suggestion.result.overflow}.`,
    ]);
    return result('suggest-wires','thoughtful','Now investigate the wires.',[
      'Can you make a connection shorter?',
      'Keep each region at 2 points or fewer.',
    ]);
  }

  // A transfer or preset is a fresh observation, not an earned improvement.
  const compare=before&&!['initial','transfer','preset'].includes(action);
  if(compare&&delta.overflow<0){
    if(m.overflow===0)return result('capacity-solved','success',"That's good: every region fits.",[
      `${overflowLine} Capacity is met.`,wireLine+(delta.hpwl>1e-7?' A trade-off.':''),
    ],delta.hpwl>1e-7?'The extra wirelength bought room for the points.': 'The move improves the capacity score.');
    return result('less-crowded','success',"That's better. More room!",[
      `${overflowLine} Keep going.`,wireLine+(delta.hpwl>1e-7?' A trade-off.':''),
    ]);
  }
  if(compare&&delta.overflow>0)return result('more-crowded','warning','Too crowded again.',[
    countLine,`${overflowLine} Try another region.`,
  ],'A shorter wire is not enough if a region exceeds its capacity.');
  if(compare&&delta.hpwl< -1e-7){
    if(m.overflow===0)return result('shorter-and-feasible','success',"That's good: shorter wires.",[
      wireLine,'Every region still fits.',
    ]);
    return result('shorter-but-crowded','thoughtful','Shorter wires, still crowded.',[
      wireLine,`${overflowLine} We still need room.`,
    ]);
  }
  if(compare&&delta.hpwl>1e-7){
    if(m.overflow===0)return result('longer-but-feasible','thoughtful','The regions still fit.',[
      `${wireLine} Wires grew.`, 'Could you keep the room, lose the length?',
    ]);
    return result('longer-still-crowded','warning','The crowding has not improved.',[
      `${wireLine} Wires grew.`, `${overflowLine} Try a roomier region.`,
    ]);
  }
  if(compare&&near(delta.overflow,0)&&near(delta.hpwl,0))return result('same-scores','neutral','A small move; the same scores.',[
    `HPWL ${f(m.hpwl)}. Overflow ${m.overflow}.`,
    m.overflow?'Cross into a region with a free place.':'Every region still fits.',
  ],'Movement alone does not necessarily change either score.');
  if(m.overflow>0)return result(action==='transfer'?'transfer-crowded':'observe-crowded','warning','Too crowded here.',[
    countLine,`We need room for ${m.overflow} extra point${m.overflow===1?'':'s'}.`,
  ]);
  return result(action==='transfer'?'transfer-feasible':'observe-feasible','neutral','Every region has enough room.',[
    'Overflow is zero. Capacity is met.',`${wireLine} Can you shorten it?`,
  ]);
}
